<?php
function query_cus_mould($params)
{ //查詢該客戶所擁有的機台型號
    $cus_id = $params->cus_id;
    $whereAttr = new stdClass();
    $whereAttr->cus_id = [$cus_id];
    $symbols = new stdClass();
    $symbols->cus_id = ['equal'];
    $data = array(
        'condition_1' => array(
            'table' => 'device_basic',
            'where' => $whereAttr,
            'symbols' => $symbols,
            'limit' => ['ALL'],
        )
    );
    $machine_model = CommonSqlSyntax_Query($data, "MySQL");
    if ($machine_model['Response'] !== 'ok') {
        return array(
            'Response' => "no data"
        );
    }
    $machine_model_data = $machine_model['QueryTableData'];

    $device_model_array = array();
    foreach ($machine_model_data as $value) {
        array_push($device_model_array, $value['model']);
    }
    $device_model_array_unique = array_unique($device_model_array);
    $return_model_obj = array();
    foreach ($device_model_array_unique as $value) {
        $temp_obj = array(
            'text' => $value,
            'value' => $value,
        );
        array_push($return_model_obj, $temp_obj);
    }
    $return_data = array(
        'Response' => "ok",
        'QueryTableData' => $return_model_obj
    );
    return $return_data;
}
function query_model_light_list($params)
{   //查詢該機台使用啟用的感測器
    $model = $params->model;
    $query_model_light_list = new apiJsonBody_queryJoin;
    $query_model_light_list->addFields('model_light_list', ['model']);
    $query_model_light_list->addFields('light_list', ['light_code', 'light_name']);
    $query_model_light_list->setTables(['model_light_list', 'light_list']);
    $join = new stdClass();
    $join->model_light_list = [];
    $model_light_list = new stdClass();
    $model_light_list->light_list = new stdClass();
    $model_light_list->light_list->light_id = new stdClass();
    $model_light_list->light_list->light_id = "id";
    array_push($join->model_light_list, $model_light_list);
    $query_model_light_list->setJoin($join);
    $query_model_light_list->addJointype('model_light_list', 'light_list', 'inner');
    $query_model_light_list->addSymbols('model_light_list', 'model', 'equal');
    $query_model_light_list->addWhere('model_light_list', 'model', $model); //型號
    $query_model_light_list->addSymbols('model_light_list', 'enable', 'equal');
    $query_model_light_list->addWhere('model_light_list', 'enable', 'Y');
    $query_model_light_list->setLimit([0, 99999]);
    $query_model_light_list_data = $query_model_light_list->getApiJsonBody();
    $model_light_list = CommonSqlSyntaxJoin_Query($query_model_light_list_data, "MySQL", "no");
    if ($model_light_list['Response'] !== 'ok') {
        $model_light_list_data = [];
    } else {
        $model_light_list_data = $model_light_list['QueryTableData'];
    }
    $return_model_light_list = array();
    foreach ($model_light_list_data as $value) {
        array_push($return_model_light_list, array(
            'text' => $value['light_list$light_name'],
            'value' => $value['light_list$light_code']
        ));
    }
    $return_data = array(
        'Response' => 'ok',
        'QueryTableData' => $return_model_light_list
    );
    return $return_data;
}
function add_new_combine($params)
{
    $model = $params->model;
    $cus_id = $params->cus_id;
    //使用者要新增的組合
    $combineData = $params->combineData;
    $user_combine_array = array();
    foreach ($combineData as $value) {
        $status_temp = array();
        foreach ($value->status as $status_value) {
            array_push($status_temp, $status_value->sensorCode . "-" . $status_value->sensorSetting);
        }
        array_push($user_combine_array, $status_temp);
    }

    //資料庫已經存在的組合
    $fields = ['model', 'light_list'];
    $whereAttr = new stdClass();
    $whereAttr->model = [$model];
    $symbols = new stdClass();
    $symbols->model = ['equal'];
    $data = array(
        'condition_1' => array(
            'table' => 'light_error_list',
            'fields' => $fields,
            'where' => $whereAttr,
            'symbols' => $symbols,
            'limit' => ['ALL'],
        )
    );
    $light_error_list = CommonSqlSyntax_Query($data, "MySQL");
    if ($light_error_list['Response'] == 'ok') {
        $light_error_list_data = $light_error_list['QueryTableData'];
    } else {
        $light_error_list_data = [];
    }
    $sql_combine_array = array();
    foreach ($light_error_list_data as $value) {
        $light_list = json_decode($value['light_list']);
        $light_list_temp = array();
        foreach ($light_list as $light_list_key => $light_list_value) {
            array_push($light_list_temp, $light_list_key . "-" . $light_list_value);
        }
        array_push($sql_combine_array, $light_list_temp);
    }

    //與資料庫比較，取出重複的組合
    $combine_result = check_repeat($sql_combine_array, $user_combine_array);
    $repeat_combine = $combine_result['repeat_combine'];

    if (count($repeat_combine) > 0) {
        return array(
            'Response' => 'add_new_combine_repeat',
            'repeat_data' => $repeat_combine
        );
    } else {
        //新增進資料庫
        $add_data = array(
            'id' =>array(),
            'model' => array(),
            'err_name' => array(),
            'err_solution' => array(),
            'light_list' => array(),
            'creator'=>array(),
            'modifier'=>array(),
        );
        foreach ($combineData as $value) {
            $status_json = array();
            foreach ($value->status as $s_value) {
                $status_json[$s_value->sensorCode] = $s_value->sensorSetting;
            }
            array_push($add_data['id'],"");
            array_push($add_data['light_list'], json_encode($status_json));
            array_push($add_data['err_name'], $value->reason);
            array_push($add_data['err_solution'], $value->solution);
            array_push($add_data['model'], $model);
            array_push($add_data['creator'], $cus_id);
            array_push($add_data['modifier'], $cus_id);
        }
        $add_data = CommonCreate($add_data, 'MySQL', 'light_error_list');
        if ($add_data["Response"] == 'ok') {
            return array(
                'Response' => 'add_new_combine_success'
            );
        }
    }

    return $repeat_combine;
}
function check_repeat($sql_value, $user_input_value)
{
    $a = $sql_value;
    $b = $user_input_value;

    $a_test = array();

    foreach ($a as $key => $value) {
        if (!isset($a_test[count($value)])) {
            $a_test[count($value)] = array();
        }
        array_push($a_test[count($value)], $value);
    }

    $repeat_combine = array();
    foreach ($b as $first_key => $first_value) {
        if (isset($a_test[count($first_value)])) {
            $check = checkB($a_test[count($first_value)], $first_value);
        } else {
            $a_test[count($first_value)] = array();
            $check = true;
        }
        if ($check) {
            array_push($a, $first_value);
            array_push($a_test[count($first_value)], $first_value);
            // array_push($add_new, $first_value);
        } else {
            //回覆重複的值
            array_push($repeat_combine, $first_key);
        }
    }

    return array(
        'repeat_combine' => $repeat_combine,
    );
}


function checkB($a_test, $first_value)
{
    foreach ($a_test as $a_key => $a_value) {
        $c = array_diff($a_value,  $first_value);
        if (count($c) == 0) {
            return false;
        }
    }
    return true;
}

function query_light_error_list($params){
    $cus_id = $params->cus_id;
    $model = $params->model;
    $fields = ['id','model', 'light_list','err_name','err_solution'];
    $whereAttr = new stdClass();
    $whereAttr->model = [$model];
    $symbols = new stdClass();
    $symbols->model = ['equal'];
    $data = array(
        'condition_1' => array(
            'table' => 'light_error_list',
            'fields'=>$fields ,
            'where' => $whereAttr,
            'symbols' => $symbols,
            'limit' => ['ALL'],
        )
    );
    $light_error_list = CommonSqlSyntax_Query($data, "MySQL");
    if ($light_error_list['Response'] !== 'ok') {
        $light_error_list_data = [];
    } else {
        $light_error_list_data = $light_error_list['QueryTableData'];
    }

    //查詢該機台使用啟用的感測器
    $model = $params->model;
    $query_model_light_list = new apiJsonBody_queryJoin;
    $query_model_light_list->addFields('model_light_list', ['model']);
    $query_model_light_list->addFields('light_list', ['light_code', 'light_name']);
    $query_model_light_list->setTables(['model_light_list', 'light_list']);
    $join = new stdClass();
    $join->model_light_list = [];
    $model_light_list = new stdClass();
    $model_light_list->light_list = new stdClass();
    $model_light_list->light_list->light_id = new stdClass();
    $model_light_list->light_list->light_id = "id";
    array_push($join->model_light_list, $model_light_list);
    $query_model_light_list->setJoin($join);
    $query_model_light_list->addJointype('model_light_list', 'light_list', 'inner');
    $query_model_light_list->addSymbols('model_light_list', 'model', 'equal');
    $query_model_light_list->addWhere('model_light_list', 'model', $model); //型號
    $query_model_light_list->addSymbols('model_light_list', 'enable', 'equal');
    $query_model_light_list->addWhere('model_light_list', 'enable', 'Y');
    $query_model_light_list->setLimit([0, 99999]);
    $query_model_light_list_data = $query_model_light_list->getApiJsonBody();
    $model_light_list = CommonSqlSyntaxJoin_Query($query_model_light_list_data, "MySQL", "no");
    if ($model_light_list['Response'] !== 'ok') {
        $model_light_list_data = [];
    } else {
        $model_light_list_data = $model_light_list['QueryTableData'];
    }


   

    $model_light_list_bind_key = array();
    foreach($model_light_list_data as $value){
        $model_light_list_bind_key[$value['light_list$light_code']] = array(
          'light_code'=>$value['light_list$light_code'],
          'light_name'=>$value['light_list$light_name'],
          'model'=>$value['model_light_list$model']
        );
    }
    foreach($light_error_list_data as $key => $value){
        $light_list = json_decode($value['light_list']);
        $ligth_list_text = array();
        foreach($light_list as $light_list_key => $light_list_value){
            $light_name = $model_light_list_bind_key[$light_list_key]["light_name"];
            if($light_list_value == 0){
                $status = "異常";
            }else{
                $status = "正常";
            }
            array_push($ligth_list_text,$light_name . "-" . $status);
        }
        $light_error_list_data[$key]['light_list_text'] = $ligth_list_text;
    }
    $return_data = array(
        'Response' => 'ok',
        'QueryTableData' => array()
    );
    foreach($light_error_list_data as $value){
        $temp_obj = array(
            'status' =>$value['light_list_text'],
            'reason' =>$value['err_name'],
            'solution' =>$value['err_solution'],
            'id' => $value['id'],
            'model' => $value['model'],
            'light_list' => json_decode($value['light_list']),
        );
        array_push($return_data['QueryTableData'],$temp_obj);
    }
    return $return_data;
}

function UpdateLightErrorList($params){
    $model = $params->model;
    $mod_id = $params->mod_id;
    $combineData = $params->combineData;
    // return  $combineData;
    $user_combine_array = array();
    // foreach ($combineData as $value) {
        $status_temp = array();
        foreach ($combineData->status as $status_value) {
            array_push($status_temp, $status_value->sensorCode . "-" . $status_value->sensorSetting);
        }
        array_push($user_combine_array, $status_temp);
    // }
    
    //資料庫已經存在的組合
    $fields = ['model', 'light_list'];
    $whereAttr = new stdClass();
    $whereAttr->model = [$model];
    $whereAttr->id = [$mod_id];
    $symbols = new stdClass();
    $symbols->model = ['equal'];
    $symbols->id = ['notequal'];
    $data = array(
        'condition_1' => array(
            'table' => 'light_error_list',
            'fields' => $fields,
            'where' => $whereAttr,
            'symbols' => $symbols,
            'limit' => ['ALL'],
        )
    );
    $light_error_list = CommonSqlSyntax_Query($data, "MySQL");
    if ($light_error_list['Response'] == 'ok') {
        $light_error_list_data = $light_error_list['QueryTableData'];
    } else {
        $light_error_list_data = [];
    }
    $sql_combine_array = array();
    foreach ($light_error_list_data as $value) {
        $light_list = json_decode($value['light_list']);
        $light_list_temp = array();
        foreach ($light_list as $light_list_key => $light_list_value) {
            array_push($light_list_temp, $light_list_key . "-" . $light_list_value);
        }
        array_push($sql_combine_array, $light_list_temp);
    }
    
    $combine_result = check_repeat($sql_combine_array, $user_combine_array);
    $repeat_combine = $combine_result['repeat_combine'];

    if (count($repeat_combine) > 0) {
        return array(
            'Response' => 'update_new_combine_repeat',
            'repeat_data' => $repeat_combine
        );
    } else {
        //新增進資料庫
        $update_data = array(
            'old_id' => array(),
            'old_model' => array(),
            'err_name' => array(),
            'err_solution' => array(),
            'light_list' => array(),
        );
        // foreach ($combineData as $value) {
            $status_json = array();
            foreach ($combineData->status as $s_value) {
                $status_json[$s_value->sensorCode] = $s_value->sensorSetting;
            }
            array_push($update_data['old_id'], $mod_id);
            array_push($update_data['old_model'], $model);
            array_push($update_data['light_list'], json_encode($status_json));
            array_push($update_data['err_name'], $combineData->reason);
            array_push($update_data['err_solution'], $combineData->solution);
        // }
        $update_data = CommonUpdate($update_data, 'MySQL', 'light_error_list');
        return $update_data;
        if ($update_data["Response"] == 'ok') {
            return array(
                'Response' => 'add_new_combine_success'
            );
        }

    }

    return $repeat_combine;
}

function DeleteLightErrorList($params){
    $del_id = $params->del_id;
    $data = array(
        'id' => array($del_id)
    );
    $light_error_list = CommonDelete($data, "MySQL", "light_error_list");

    $return_data = array();
    $return_data['Response'] = $light_error_list['Response'];
    return $return_data;
}