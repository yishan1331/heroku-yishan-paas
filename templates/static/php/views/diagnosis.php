<?php
ini_set('memory_limit', '1024M');
set_time_limit(180);
function MainQuery($params)//主要查詢按鈕
{
    $cus_id = $params->cusID;
    $device_id = $params->deviceID;
    $model = $params->model;
    $user_start_time = date("Y-m-d 08:00:00", strtotime($params->startTime));
    $user_end_time = date("Y-m-d 08:00:00", strtotime($params->endTime)+86400);

    $device_light_data = get_device_light($device_id);
    $light_error_list_data = get_light_error_list($model);

    $check_group_list = array();
    foreach ($light_error_list_data as $device_model => $device_light_list) {
        foreach ($device_light_list as $light_list_value) {
            if (!empty($light_list_value['light_list'])) {
                if (is_string($light_list_value['light_list'])) {
                    $light_list_value['light_list'] = json_decode($light_list_value['light_list'], true);
                }
                $light_list = $light_list_value['light_list'];
                $group_list = array();
                foreach ($light_list as $light_code => $light_status) {
                    if (!isset($device_light_data[$device_model . '_' . $device_id][$light_code])) {
                        break;
                    }
                    $erro_value = $device_light_data[$device_model . '_' . $device_id][$light_code]['erro_value'];
                    if (!$light_status) {
                        $group_list[$light_code] = $erro_value;
                    } else {
                        $group_list[$light_code] = $erro_value ? 0 : 1;
                    }
                }
                array_push($check_group_list, array(
                    'light_list' => $group_list,
                    'name' => $light_list_value['name'],
                    'solution' => $light_list_value['solution']
                ));
            }
        }
    }
    usort($check_group_list, 'sort_light_error_list_time');

    $light_code_array = array_keys($device_light_data[$model.'_'.$device_id]);
    $device_detail = get_device_detail($user_start_time, $user_end_time, $cus_id, $device_id, $light_code_array);
    if ($device_detail['Response'] !== 'ok') {
        return $device_detail;
    }
    $device_detail_data = $device_detail['QueryTableData'];
    
    $device_detail_time_data = get_device_detail_time($device_detail_data, $light_code_array);

    $diagnosis_data = array();
    foreach ($device_detail_time_data as $key => $value) {
        foreach ($check_group_list as $group_list) {
            $check_ok = false;
            $this_light_list_array = array();
            foreach ($group_list['light_list'] as $light_code => $light_value) {
                if (!isset($value[$light_code])) {
                    break;
                }
                if ($value[$light_code] != $light_value) {
                    break;
                } else {
                    array_push($this_light_list_array, $light_code);
                }
                $check_ok = true;
            }
            if ($check_ok) {
                foreach ($this_light_list_array as $light_code) {
                    unset($value[$light_code]);
                }
                if ($value['startTime'] == $value['endTime']) {
                    $durationTime = ['00:00:00'];
                } else {
                    $durationTime = TimeSubtraction($value['startTime'], $value['endTime'], 'hour');
                }
                array_push($diagnosis_data, array(
                    'reason' => $group_list['name'],
                    'solution' => $group_list['solution'],
                    'startTime' => $value['startTime'],
                    'endTime' => $value['endTime'],
                    'duration' => $durationTime[0]
                ));
                // break;
            }
        }
    }
    
    $returnData['QueryTableData'][0]['device_detail_data'] = $diagnosis_data;
    $returnData['Response'] = 'ok';
    return  $returnData;
}

function SelectOption($params)
{
    //回傳的資料
    $returnData['QueryTableData'] = [];

    $cus_id = $params->cusID;

    //查詢所有機台
    $device = CommonSpecificKeyQuery('Redis', $cus_id . '_*', 'yes');
    if ($device['Response'] !== 'ok') {
        return;
    }
    $device_data = $device['QueryValueData'];

    $model_array = array();
    $device_array = array();
    foreach ($device_data as $key => $value) {
        $this_device_model = $value['device_model'];
        $this_device_id = $value['device_id'];
        $this_device_name = $value['device_name'];
        if (gettype(array_search($this_device_model.'', array_column($model_array, 'value'))) == 'boolean') {
            array_push($model_array, array(
                'value' => $this_device_model,
                'text' => $this_device_model,
            ));
        }
        if (!isset($device_array[$this_device_model])) {
            $device_array[$this_device_model] = array();
        }
        array_push($device_array[$this_device_model], array(
            'value' => $this_device_id,
            'text' => $this_device_name,
        ));
    }
    sort($model_array);
    foreach ($device_array as $key => $value) {
        usort($device_array[$key], 'sort_device');
    }
    array_push($returnData['QueryTableData'], array(
        'model' => $model_array,
        'device' => $device_array
    ));

    $returnData['Response'] = 'ok';
    return $returnData;
}

function sort_device($a, $b){
    return ($a['value'] > $b['value']) ? 1 : -1;
}

//機台燈號
function get_device_light($device_id)
{
    if (empty($device_id)) {
        return array();
    }

    $query_device_basic = new apiJsonBody_queryJoin;
    $query_device_basic->addFields('device_basic', ['id', 'model']);
    $query_device_basic->addFields('light_list', ['light_code', 'color_on', 'color_off']);
    $query_device_basic->setTables(['device_basic', 'machine_light_list', 'light_list']);
    $join = new stdClass();
    $join->device_basic = [];
    $machine_light_list = new stdClass();
    $machine_light_list->machine_light_list = new stdClass();
    $machine_light_list->machine_light_list->id = new stdClass();
    $machine_light_list->machine_light_list->id = "device_id";
    $machine_light_list->machine_light_list->JOIN = new stdClass();
    $machine_light_list->machine_light_list->JOIN->light_list = new stdClass();
    $machine_light_list->machine_light_list->JOIN->light_list->light_id = new stdClass();
    $machine_light_list->machine_light_list->JOIN->light_list->light_id = "id";
    array_push($join->device_basic, $machine_light_list);
    $query_device_basic->setJoin($join);
    $query_device_basic->addJointype('device_basic', 'machine_light_list', 'inner');
    $query_device_basic->addJointype('machine_light_list', 'light_list', 'inner');
    $query_device_basic->addSymbols('device_basic', 'id', 'equal');
    $query_device_basic->addWhere('device_basic', 'id', $device_id);
    $query_device_basic->addSymbols('machine_light_list', 'light_enable', 'equal');
    $query_device_basic->addWhere('machine_light_list', 'light_enable', 'Y');
    $query_device_basic->setLimit([0,99999]);
    $query_device_basic_data = $query_device_basic->getApiJsonBody();
    $device_basic = CommonSqlSyntaxJoin_Query($query_device_basic_data, "MySQL", "no");
    if ($device_basic['Response'] !== 'ok') {
        $device_basic_data = [];
    } else {
        $device_basic_data = $device_basic['QueryTableData'];
    }

    $mes_device = array();
    foreach ($device_basic_data as $key => $value) {
        if (!isset($mes_device[$value['device_basic$model'] . '_' . $value['device_basic$id']])) {
            $mes_device[$value['device_basic$model'] . '_' . $value['device_basic$id']] = array();
        }
        if (!isset($mes_device[$value['device_basic$model'] . '_' . $value['device_basic$id']][$value['light_list$light_code']])) {
            $mes_device[$value['device_basic$model'] . '_' . $value['device_basic$id']][$value['light_list$light_code']] = array();
        }
        if ($value['light_list$color_on'] == 'red') {
            $erro_value = 1;
        } else if ($value['light_list$color_off'] == 'red') {
            $erro_value = 0;
        }
        $mes_device[$value['device_basic$model'] . '_' . $value['device_basic$id']][$value['light_list$light_code']] = array(
            'erro_value' => isset($erro_value) ? $erro_value : null
        );
    }

    return $mes_device;
}

//機台燈號異常表
function get_light_error_list($model)
{
    if (empty($model)) {
        return array();
    }

    $query_light_error_list = new apiJsonBody_query;
    $query_light_error_list->setFields(['model', 'light_list', 'err_name', 'err_solution']);
    $query_light_error_list->setTable('light_error_list');
    $query_light_error_list->addSymbols('model', 'equal');
    $query_light_error_list->addWhere('model', $model);
    $query_light_error_list_data = $query_light_error_list->getApiJsonBody();
    $light_error_list = CommonSqlSyntax_Query($query_light_error_list_data, "MySQL", "no");
    if ($light_error_list['Response'] !== 'ok') {
        $light_error_list_data = [];
    } else {
        $light_error_list_data = $light_error_list['QueryTableData'];
    }

    $mes_device = array();
    foreach ($light_error_list_data as $key => $value) {
        if (!isset($mes_device[$value['model']])) {
            $mes_device[$value['model']] = array();
        }//機台燈號異常表
        array_push($mes_device[$value['model']], array(
            'light_list' => $value['light_list'],
            'name' => $value['err_name'],
            'solution' => $value['err_solution'],
        ));
    }

    return $mes_device;
}

//查詢機台資料
function get_device_detail($user_start_time, $user_end_time, $cus_id, $device_id, $light_code_array)
{
    $data = array(
        'condition_1' => array(
            // 'fields' => $light_code_array,
            'fields' => "",
            'intervaltime' => array(
                "upload_at" => array([$user_start_time, $user_end_time])
            ),
            'table' => $cus_id . '_' . $device_id . '_main',
            'orderby' => ["asc", "upload_at"],
            'limit' => ["ALL"],
            'where' => "",
            'symbols' => "",
            'union' => "",
            'subquery' => ""
        )
    );
    try {
        global $publicIP,$publicPort;
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/2.5/myps/Sensor/SqlSyntax?uid=@sapido@PaaS&dbName=site2&getSqlSyntax=yes";
        $ch = curl_init($url);
    
        // Check if initialization had gone wrong*    
        if ($ch === false) {
            throw new Exception('failed to initialize');
        }

        curl_setopt($ch, CURLOPT_HTTPHEADER, array(
            'Content-Type: application/json',
            'Content-Length: ' . strlen(json_encode($data)))
        );
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "POST");
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, '0');
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, '0');
        // curl_setopt(/* ... */);
    
        $content = curl_exec($ch);
        $result = json_decode($content, true);

        // Check the return value of curl_exec(), too
        if ($content === false) {
            throw new Exception(curl_error($ch), curl_errno($ch));
        }
        /* Process $content here */
        
        // Close curl handle
        curl_close($ch);
        return $result;
    } catch(Exception $e) {
        return array('Response' => $e);
        // trigger_error(sprintf(
        //     'Curl failed with error #%d: %s',
        //     $e->getCode(), $e->getMessage()),
        //     E_USER_ERROR);
    }
}

//異常長度排序
function sort_light_error_list_time($a, $b)
{
    return (count($a['light_list']) > count($b['light_list'])) ? -1 : 1;
}

//整理機台資料時間
function get_device_detail_time($device_detail_data, $light_code_array)
{
    if (empty($device_detail_data)) {
        return [];
    }
    $machine_detail_old_Data = [];
    $machine_detail_now_Detail = [];
    $machine_detail_now_Status = [];
    $machine_detail_now_Status_Time = [];
    foreach ($device_detail_data as $key => $value) {
        $machine_detail = $value;
        if (empty($machine_detail['upload_at'])) {
            continue;
        }
        $chain_this_data = array();
        foreach ($light_code_array as $light_code) {
            $chain_this_data[$light_code] = $machine_detail[$light_code];
        }

        if (count($machine_detail_old_Data) == 0) {
            $machine_detail_old_Data = $chain_this_data;//儲存當作比對的物件
            $machine_detail_now_Status = $chain_this_data;//儲存現在的物件
            array_push($machine_detail_now_Status_Time, $machine_detail['upload_at']);//第一筆為開始，第二筆為結束
        } else {
            if ($key < count($device_detail_data) - 1) {//確認不是最後一筆
                if (count(array_keys(array_diff_assoc($chain_this_data, $machine_detail_old_Data))) == 0) {//判斷是否一樣，如果一樣就儲存最後的時間
                    $machine_detail_now_Status = $machine_detail_old_Data;
                    $machine_detail_now_Status_Time[1] = $machine_detail['upload_at'];
                } else {//如果不一樣，儲存最後的時間，並記錄到陣列中，在開始一筆新的紀錄
                    $machine_detail_now_Status = $machine_detail_old_Data;
                    $machine_detail_now_Status_Time[1] = $machine_detail['upload_at'];
                    $machine_detail_now_Detail[count($machine_detail_now_Detail)] = $machine_detail_now_Status;
                    $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['startTime'] = $machine_detail_now_Status_Time[0];
                    $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['endTime'] = $machine_detail_now_Status_Time[1];
                 
                    $machine_detail_old_Data = $chain_this_data;
                    $machine_detail_now_Status = $machine_detail_old_Data;
                    $machine_detail_now_Status_Time = [];
                    array_push($machine_detail_now_Status_Time, $machine_detail['upload_at']);
                }
            } else {//最後一筆，儲存最後的時間，並記錄到陣列中
                $machine_detail_now_Status = $machine_detail_old_Data;
                $machine_detail_now_Status_Time[1] = $machine_detail['upload_at'];
                $machine_detail_now_Detail[count($machine_detail_now_Detail)] = $machine_detail_now_Status;
                $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['startTime'] = $machine_detail_now_Status_Time[0];
                $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['endTime'] = $machine_detail_now_Status_Time[1];
            }
        }
    }

    return $machine_detail_now_Detail;
}

function query_cus_list()
{
    $query_customer = CommonTableQuery('MySQL', 'customer');
    if ($query_customer['Response'] !== 'ok') {
        return array(
            'Response' => "no data"
        );
    }
    $customer_data = $query_customer['QueryTableData'];
    $return_customer_data = array();
    foreach ($customer_data as $value) {
        $data_obj = array(
            'text' => $value['cus_name'],
            'value' => $value['id']
        );
        array_push($return_customer_data,$data_obj);
    }
    $return_data = array(
        'customer_data' => $return_customer_data,
        'Response' => "ok"
    );
    return $return_data;
}