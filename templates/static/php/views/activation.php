<?php
function MainQuery($params)//主要查詢按鈕
{
    $device_id = $params->deviceID;

    $query_now_status = false;
    $now_date = date("Y-m-d");
    $now_date_time = date("Y-m-d H:i:s");
    $user_start_time = strtotime($params->startTime);
    if (strtotime(date("Y-m-d", strtotime($params->endTime))) >= strtotime($now_date)) {
        if ($user_start_time < strtotime(date("Y-m-d 23:59:59"))) {
            $query_now_status = true;
        }
        $start_date_time = date("Y-m-d 08:00:00", $user_start_time+86400);
        if (strtotime($start_date_time) > strtotime($now_date_time)) {
            $end_date_time = date("Y-m-d H:i:s", strtotime($start_date_time)+1);
        } else {
            $end_date_time = $now_date_time;
        }
    } else {
        $start_date_time = date("Y-m-d 08:00:00", $user_start_time+86400);
        //查詢截止時間若小於今天，則截止時間加一天來做查詢資料(machine_status_sum為隔天7點運算)
        $end_date_time = date("Y-m-d 23:59:59", strtotime($params->endTime)+86400);
    }

    if (isset($device_id)) {
        $symbols = new stdClass();
        $symbols->device_id = ['equal'];
        $whereAttr = new stdClass();
        $whereAttr->device_id = [$device_id];
    }
    $data = array(
        'condition_1' => array(
            'intervaltime' => array('upload_at' => array(array($start_date_time, $end_date_time))),
            'table' => 'machine_status_sum',
            'where' => isset($whereAttr)?$whereAttr:'',
            'limit' => ['ALL'],
            'orderby' => ['asc', 'upload_at'],
            'symbols' => isset($symbols)?$symbols:''
        )
    );

    $machine_status_sum = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");

    if ($machine_status_sum['Response'] !== 'ok') {
        return $machine_status_sum;
    } else if (count($machine_status_sum['QueryTableData']) == 0) {
        // $returnData['Response'] = 'no data';
        // return $returnData;
    }
    $Query_Device_Response = $machine_status_sum['QueryTableData'];

    if ($query_now_status == true) {
        $cus_id = $params->cusID;

        $device = CommonSpecificKeyQuery('Redis', $cus_id . '_' . $device_id, 'no');
        if ($device['Response'] !== 'ok') {
            return $device;
        }
        $this_device_data = $device['QueryValueData'];

        array_push($Query_Device_Response, array(
            'device_id' => $device_id,
            'machine_detail' => array(
                'R' => array(
                    'datail' => [],
                    'rate' => $this_device_data['device_activation']
                )
            ),
            'upload_at' => date("Y-m-d", strtotime($now_date_time)+86400)
        ));

        // $Query_Device_data = Query_Device(date("Y-m-d 08:00:00"), $now_date_time, isset($device_id)?$device_id:null, isset($params->process)?$params->process:null);
        // for ($i=0; $i < count($Query_Device_data); $i++) { 
        //     $Query_Device_data[$i]['upload_at'] = date("Y-m-d", strtotime($now_date_time)+86400);
        //     array_push($Query_Device_Response, $Query_Device_data[$i]);
        // }
    }

    if (empty($Query_Device_Response)) {
        $returnData['Response'] = 'no data';
        return $returnData;
    }

    $device_data_day = array(
        'data' => [],
        'data_time' => []
    );
    $device_data_week = array(
        'data' => [],
        'data_time' => []
    );
    $device_data_month = array(
        'data' => [],
        'data_time' => []
    );
    $device_data_year = array(
        'data' => [],
        'data_time' => []   
    );
    $device_detail_data = array();
    foreach ($Query_Device_Response as $key => $status_value) {
        //因為都是在隔天7點結算，所以儲存的時間需要減一天
        $this_data_time = date("Y-m-d", strtotime($status_value['upload_at'])-86400);
        $this_week = (int)strftime('%U', strtotime($status_value['upload_at'])) + 1;
        $this_date = explode("-", $this_data_time);
        //紀錄圖表X座標時間
        if (!in_array($this_date[0] . '年' . $this_date[1] . '月' . $this_date[2] . '日', $device_data_day['data_time'])) {
            array_push($device_data_day['data_time'], $this_date[0] . '年' . $this_date[1] . '月' . $this_date[2] . '日');
        }
        if (!in_array($this_week . '周', $device_data_week['data_time'])) {
            array_push($device_data_week['data_time'], $this_week . '周');
        }
        if (!in_array($this_date[0] . '年' . $this_date[1] . '月', $device_data_month['data_time'])) {
            array_push($device_data_month['data_time'], $this_date[0] . '年' . $this_date[1] . '月');
        }
        if (!in_array($this_date[0] . '年', $device_data_year['data_time'])) {
            array_push($device_data_year['data_time'], $this_date[0] . '年');
        }
        //圖表y座標，與年和月的資料筆數
        if ($status_value['device_id'] == 'test_main') {
            $status_value['device_id'] = 'F01';
        }
        if (!isset($device_data_day['data'][$status_value['device_id']])) {
            $device_data_day['data'][$status_value['device_id']] = array('data' => []);
        }
        if (!isset($device_data_week['data'][$status_value['device_id']])) {
            $device_data_week['data'][$status_value['device_id']] = array('data' => [], 'data_qty' => []);
        }
        if (!isset($device_data_month['data'][$status_value['device_id']])) {
            $device_data_month['data'][$status_value['device_id']] = array('data' => [], 'data_qty' => []);
        }
        if (!isset($device_data_year['data'][$status_value['device_id']])) {
            $device_data_year['data'][$status_value['device_id']] = array('data' => [], 'data_qty' => []);
        }

        // //加總運轉時間
        // $this_run_day_time = 0;
        // foreach ($status_value['machine_detail']['R']['datail'] as $run_key => $run_value) {
        //     $this_run_day_time += strtotime($run_value['timestamp'][1]) - strtotime($run_value['timestamp'][0]);
        // }
        //計算當日稼動率
        $this_activation = (float)$status_value['machine_detail']['R']['rate'];

        //紀錄圖表y座標，與年和月的資料筆數
        $position = array_search($this_date[0] . '年' . $this_date[1] . '月' . $this_date[2] . '日', $device_data_day['data_time']);
        if (!isset($device_data_day['data'][$status_value['device_id']]['data'][$position])) {
            $device_data_day['data'][$status_value['device_id']]['data'][$position] = $this_activation;
        }
        $position = array_search($this_week . '周', $device_data_week['data_time']);
        if (!isset($device_data_week['data'][$status_value['device_id']]['data'][$position])) {
            $device_data_week['data'][$status_value['device_id']]['data'][$position] = $this_activation;
            $device_data_week['data'][$status_value['device_id']]['data_qty'][$position] = 1;
        } else {
            $device_data_week['data'][$status_value['device_id']]['data'][$position] += $this_activation;
            $device_data_week['data'][$status_value['device_id']]['data_qty'][$position]++;
        }
        $position = array_search($this_date[0] . '年' . $this_date[1] . '月', $device_data_month['data_time']);
        if (!isset($device_data_month['data'][$status_value['device_id']]['data'][$position])) {
            $device_data_month['data'][$status_value['device_id']]['data'][$position] = $this_activation;
            $device_data_month['data'][$status_value['device_id']]['data_qty'][$position] = 1;
        } else {
            $device_data_month['data'][$status_value['device_id']]['data'][$position] += $this_activation;
            $device_data_month['data'][$status_value['device_id']]['data_qty'][$position]++;
        }
        $position = array_search($this_date[0] . '年', $device_data_year['data_time']);
        if (!isset($device_data_year['data'][$status_value['device_id']]['data'][$position])) {
            $device_data_year['data'][$status_value['device_id']]['data'][$position] = $this_activation;
            $device_data_year['data'][$status_value['device_id']]['data_qty'][$position] = 1;
        } else {
            $device_data_year['data'][$status_value['device_id']]['data'][$position] += $this_activation;
            $device_data_year['data'][$status_value['device_id']]['data_qty'][$position]++;
        }
        //紀錄表格資料
        array_push($device_detail_data, array(
            'date' => $this_data_time,
            // 'site' => '二廠',
            // 'group' => '成四組',
            // 'class' => '日班',
            // 'device_id' => $status_value['device_id'],
            'activation' => $this_activation . '%',
        ));
    }

    //計算周稼動率，並清除紀錄筆數資料
    foreach ($device_data_week['data'] as $device_id => $device_value) {
        for ($i=0; $i < count($device_value['data']); $i++) { 
            $device_data_week['data'][$device_id]['data'][$i] = round($device_value['data'][$i] / $device_value['data_qty'][$i], 2);
        }
        unset($device_data_week['data'][$device_id]['data_qty']);
    }
    //計算月份稼動率，並清除紀錄筆數資料
    foreach ($device_data_month['data'] as $device_id => $device_value) {
        for ($i=0; $i < count($device_value['data']); $i++) { 
            $device_data_month['data'][$device_id]['data'][$i] = round($device_value['data'][$i] / $device_value['data_qty'][$i], 2);
        }
        unset($device_data_month['data'][$device_id]['data_qty']);
    }
    //計算年份稼動率，並清除紀錄筆數資料
    foreach ($device_data_year['data'] as $device_id => $device_value) {
        for ($i=0; $i < count($device_value['data']); $i++) { 
            $device_data_year['data'][$device_id]['data'][$i] = round($device_value['data'][$i] / $device_value['data_qty'][$i], 2);
        }
        unset($device_data_year['data'][$device_id]['data_qty']);
    }

    if (count($device_detail_data) == 0) {
        $returnData['Response'] = '當日無稼動資料';
        return  $returnData;
    }
    $returnData['QueryTableData'][0]['device_data_day'] = $device_data_day;
    $returnData['QueryTableData'][0]['device_data_week'] = $device_data_week;
    $returnData['QueryTableData'][0]['device_data_month'] = $device_data_month;
    $returnData['QueryTableData'][0]['device_data_year'] = $device_data_year;
    $returnData['QueryTableData'][0]['device_detail_data'] = $device_detail_data;
    // $returnData['QueryTableData'][0]['query_date'] = [$params->startTime, $params->endTime, $params->model, $device_id == 'test_main' ? 'F01' : $device_id];
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

function Query_Device($startTime, $endTime, $select_device_name = null, $process = 5) {
    $now_time = $endTime;
    $previous_time = $startTime;
    $totalTime = strtotime($now_time) - strtotime($previous_time);

    //查詢所有機台
    $machine_status_head_data = Query_All_Device($select_device_name, $process);

    //查詢機台機型
    $machine_model_data = Query_machine_model($machine_status_head_data);
    
    //查詢機型燈號
    $machine_light_data = Query_machine_light($machine_model_data);

    //查詢machine_abn，機台異常資料
    $machine_abn_data = Query_All_Device_Abn();

    //取得該機台的燈號異常值
    $machine_light_abn_data = Query_machine_light_abn($machine_light_data, $machine_abn_data);

    //處理各機台
    $machine_status = [];
    foreach ($machine_status_head_data as $index => $value) {
        $device_name = $value['device_name'];
        //查詢單一機台當日資料
        $device_data = Query_Device_Data($device_name, $previous_time, $now_time);

        //將$device_data內的JSON字串轉為Object
        foreach ($device_data as $key => $value) {
            if (is_string($value['machine_detail'])) {
                $machine_detail = json_decode($value['machine_detail'], true);
                $device_data[$key]['machine_detail'] = $machine_detail;
            }
        }

        //整理取得該機台當日時間區間資料
        $device_detail_data = Get_Device_Detail_Time($device_data, $machine_light_abn_data[$device_name], $previous_time, $process);

        //若當日有資料才做
        if (!empty($device_detail_data)) {
            //整理出運轉時間
            [$machine_status_R] = Device_Status_Time($device_detail_data, $process, $machine_light_abn_data[$device_name]);

            //儲存
            $machine_status[$device_name] = array(
                'R' => array(
                    'datail' => $machine_status_R
                )
            );
        } else {
            $machine_status[$device_name] = array(
                'R' => array(
                    'rate' => '0%',
                    'datail' => []
                )
            );
        }
    }

    if (!empty($machine_status)) {
        $push_data = [];
        foreach ($machine_status as $device_name => $value) {
            array_push($push_data, array(
                'device_name' => $device_name,
                'machine_detail' => $value,
            ));
        }
    } else {
        return null;
    }
    return $push_data;
}

//查詢所有機台
function Query_All_Device($select_device_name, $process) {
    if (isset($select_device_name)) {
        $symbols = new stdClass();
        $symbols->device_name = ['equal'];
        $whereAttr = new stdClass();
        $whereAttr->device_name = [$select_device_name];
    }
    $table = '';
    if ($process == 5) {
        $table = 'machine_status_head';
    } else if ($process == 6) {
        $table = 'machine_status_thd';
    }
    $data = array(
        'condition_1' => array(
            'table' => $table,
            'where' => isset($whereAttr)?$whereAttr:'',
            'limit' => ['ALL'],
            'symbols' => isset($symbols)?$symbols:''
        )
    );
    
    $machine_status_head = CommonSqlSyntax_Query($data, "MySQL");
    if ($machine_status_head['Response'] != 'ok' || count($machine_status_head['QueryTableData']) == 0) {//先抓是否抓取成功，成功的話繼續執行
        return [];
    } else {
        return $machine_status_head['QueryTableData'];
    }
}

//查詢機台機型
function Query_machine_model($machine_status_head_data){
    $device_name = [];
    $davice_symbol = [];
    foreach ($machine_status_head_data as $key => $value) {
        array_push($device_name, $value['device_name']);
        array_push($davice_symbol, 'equal');
    }

    if (!empty($device_name)) {
        $fields = ['name', 'model'];
        $whereAttr = new stdClass();
        $whereAttr->name = $device_name;
        $symbols = new stdClass();
        $symbols->name = $davice_symbol;
        $data = array(
            'condition_1' => array(
                'fields' => $fields,
                'table' => 'device_box',
                'where' => $whereAttr,
                'symbols' => $symbols
            )
        );
        $device_box = CommonSqlSyntax_Query($data, "MsSQL");
        if ($device_box['Response'] !== 'ok') {
            return [];
        } else if (count($device_box['QueryTableData']) == 0) {
            return [];
        }
        return $device_box['QueryTableData'];
    } else {
        return [];
    }
}

//查詢機型燈號
function Query_machine_light($machine_model_data){
    $device_model = [];
    $davice_symbol = [];
    $davice_model = array();
    foreach ($machine_model_data as $key => $value) {
        array_push($device_model, $value['model']);
        array_push($davice_symbol, 'equal');
        $davice_model[$value['name']] = array(
            'model' => $value['model']
        );
    }

    if (!empty($device_model)) {
        $whereAttr = new stdClass();
        $whereAttr->model = $device_model;
        $symbols = new stdClass();
        $symbols->model = $davice_symbol;
        $data = array(
            'condition_1' => array(
                'table' => 'machine_status_list',
                'where' => $whereAttr,
                'symbols' => $symbols
            )
        );
        $machine_status_list = CommonSqlSyntax_Query($data, "MySQL");
        if ($machine_status_list['Response'] !== 'ok') {
            return [];
        } else if (count($machine_status_list['QueryTableData']) == 0) {
            return [];
        }
        $machine_status_list_data =  $machine_status_list['QueryTableData'];
    } else {
        return [];
    }
    
    foreach ($davice_model as $davice_model_key => $davice_model_value) {
        foreach ($machine_status_list_data as $machine_status_list_data_key => $machine_status_list_data_value) {
            if ($davice_model_value['model'] == $machine_status_list_data_value['model']) {
                if (is_string($machine_status_list_data_value['light_list'])) {
                    $machine_status_list_data_value['light_list'] = json_decode($machine_status_list_data_value['light_list'], true);
                }
                $davice_model[$davice_model_key]['light_list'] = $machine_status_list_data_value['light_list'];
            }
        }
    }
    return $davice_model;
}

//取得該機台的燈號異常值
function Query_machine_light_abn($machine_light_data, $machine_abn_data){
    $machine_light_abn_data = array();
    foreach ($machine_light_data as $device_name => $device_name_value) {
        if (isset($device_name_value['light_list'])) {
            foreach ($device_name_value['light_list'] as $light_key => $light_value) {
                foreach ($machine_abn_data as $machine_abn_data_key => $machine_abn_data_value) {
                    if ($light_key == $machine_abn_data_key) {
                        if (!isset($machine_light_abn_data[$device_name])) {
                            $machine_light_abn_data[$device_name] = array();
                        }
                        $machine_light_abn_data[$device_name][$light_key] = $machine_abn_data_value;
                    }
                }
            }
        }
    }
    return $machine_light_abn_data;
}

//查詢machine_abn，機台異常資料
function Query_All_Device_Abn() {
    $machine_abn = CommonTableQuery('MySQL', 'machine_abn');
    if ($machine_abn['Response'] != 'ok' || count($machine_abn['QueryTableData']) == 0) {//先抓是否抓取成功，成功的話繼續執行
        return [];
    }
    
    $machine_abn_data = $machine_abn['QueryTableData'];
    $machine_abn_code = [];
    for ($i=0; $i < count($machine_abn_data); $i++) { 
        $machine_abn_code[$machine_abn_data[$i]['name']] = array(
            'err_code' => $machine_abn_data[$i]['err_code'],
            'value' => $machine_abn_data[$i]['value'],
            'description' => $machine_abn_data[$i]['description']
        );
    }

    return $machine_abn_code;
}

//查詢單一機台當日資料
function Query_Device_Data($device_name, $previous_time, $now_time) {
    $data = array(
        'col' => 'upload_at',
        'valueStart' => $previous_time,
        'valueEnd' => $now_time
    );
    $device = CommonIntervalQuery($data, "PostgreSQL", strtolower($device_name));
    if ($device['Response'] != 'ok' || count($device['QueryTableData']) == 0) {//先抓是否抓取成功，成功的話繼續執行
        return [];
    } else {
        return $device['QueryTableData'];
    }
}

//機台新增感測項目需在此新增
//整理取得該機台當日時間區間資料
function Get_Device_Detail_Time($device_data, $machine_light_abn_data, $previous_time, $process) {
    $device_detail_data = [];
    if (!empty($device_data)) {
        $machine_detail_old_Data = [];
        $machine_detail_now_Detail = [];
        $machine_detail_now_Status = [];
        $machine_detail_now_Status_Time = [];
        if ($process == 5) {
            for ($i=0; $i < count($device_data); $i++) {
                $machine_detail = $device_data[$i]['machine_detail'];
                if (strtotime($machine_detail['timestamp']) < strtotime($previous_time)) {
                // if (strtotime($device_data[$i]['upload_at']) < strtotime($previous_time)) {
                    continue;
                }
                $chain_this_data = array();
                foreach ($machine_light_abn_data as $key => $value) {
                    $chain_this_data[$key] = $machine_detail[$key];
                }
                if (isset($machine_detail['OPR'])) {
                    $chain_this_data['OPR'] = $machine_detail['OPR'];
                } else {
                    $chain_this_data['OPR'] = 0;
                }
    
                if (count($machine_detail_old_Data) == 0) {
                    $machine_detail_old_Data = $chain_this_data;//儲存當作比對的物件
                    $machine_detail_now_Status = $chain_this_data;//儲存現在的物件
                    array_push($machine_detail_now_Status_Time, $machine_detail['timestamp']);//第一筆為開始，第二筆為結束
                    // array_push($machine_detail_now_Status_Time, $device_data[$i]['upload_at']);//時間異常，暫時用server時間
                } else {
                    if ($i < count($device_data) - 1) {//確認不是最後一筆
                        if (count(array_keys(array_diff_assoc($chain_this_data, $machine_detail_old_Data))) == 0) {//判斷是否一樣，如果一樣就儲存最後的時間
                            $machine_detail_now_Status = $machine_detail_old_Data;
                            $machine_detail_now_Status_Time[1] = $machine_detail['timestamp'];
                            // $machine_detail_now_Status_Time[1] = $device_data[$i]['upload_at'];//時間異常，暫時用server時間
                        } else {//如果不一樣，儲存最後的時間，並記錄到陣列中，在開始一筆新的紀錄
                            //如果判斷的是潤滑中再改變其餘皆正常，則視為相同狀態
                            if (count(array_keys(array_diff_assoc($chain_this_data, $machine_detail_old_Data))) == 1 && array_keys(array_diff_assoc($chain_this_data, $machine_detail_old_Data))[0] == 'in_lube') {
                                if ($chain_this_data['OPR'] == 0 && $machine_detail_old_Data['OPR'] == 0) {
                                    $machine_detail_now_Status = $machine_detail_old_Data;
                                    $machine_detail_now_Status_Time[1] = $machine_detail['timestamp'];
                                    // $machine_detail_now_Status_Time[1] = $device_data[$i]['upload_at'];//時間異常，暫時用server時間
                                    continue;
                                }
                            }
                            $machine_detail_now_Status = $machine_detail_old_Data;
                            $machine_detail_now_Status_Time[1] = $machine_detail['timestamp'];
                            // $machine_detail_now_Status_Time[1] = $device_data[$i]['upload_at'];//時間異常，暫時用server時間
                            $machine_detail_now_Detail[count($machine_detail_now_Detail)] = $machine_detail_now_Status;
                            $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['startTime'] = $machine_detail_now_Status_Time[0];
                            $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['endTime'] = $machine_detail_now_Status_Time[1];
                            $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['cnt'] = $machine_detail['cnt'];
                         
                            $machine_detail_old_Data = $chain_this_data;
                            $machine_detail_now_Status = $machine_detail_old_Data;
                            $machine_detail_now_Status_Time = [];
                            array_push($machine_detail_now_Status_Time, $machine_detail['timestamp']);
                            // array_push($machine_detail_now_Status_Time, $device_data[$i]['upload_at']);//時間異常，暫時用server時間
                        }
                    } else {//最後一筆，儲存最後的時間，並記錄到陣列中
                        $machine_detail_now_Status = $machine_detail_old_Data;
                        $machine_detail_now_Status_Time[1] = $machine_detail['timestamp'];
                        // $machine_detail_now_Status_Time[1] = $device_data[$i]['upload_at'];//時間異常，暫時用server時間
                        $machine_detail_now_Detail[count($machine_detail_now_Detail)] = $machine_detail_now_Status;
                        $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['startTime'] = $machine_detail_now_Status_Time[0];
                        $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['endTime'] = $machine_detail_now_Status_Time[1];
                        $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['cnt'] = $machine_detail['cnt'];
                    }
                }
            }
        } else if ($process == 6) {
            for ($i=0; $i < count($device_data); $i++) {
                $machine_detail = $device_data[$i]['machine_detail'];
                if (strtotime($machine_detail['timestamp']) < strtotime($previous_time)) {
                // if (strtotime($device_data[$i]['upload_at']) < strtotime($previous_time)) {
                    continue;
                }
                $chain_this_data = array();
                foreach ($machine_light_abn_data as $key => $value) {
                    $chain_this_data[$key] = $machine_detail[$key];
                }
                if (isset($machine_detail['OPR'])) {
                    $chain_this_data['OPR'] = $machine_detail['OPR'];
                } else {
                    $chain_this_data['OPR'] = 0;
                }
    
                if (count($machine_detail_old_Data) == 0) {
                    $machine_detail_old_Data = $chain_this_data;//儲存當作比對的物件
                    $machine_detail_now_Status = $chain_this_data;//儲存現在的物件
                    array_push($machine_detail_now_Status_Time, $machine_detail['timestamp']);//第一筆為開始，第二筆為結束
                    // array_push($machine_detail_now_Status_Time, $device_data[$i]['upload_at']);//時間異常，暫時用server時間
                } else {
                    if ($i < count($device_data) - 1) {//確認不是最後一筆
                        if (count(array_keys(array_diff_assoc($chain_this_data, $machine_detail_old_Data))) == 0) {//判斷是否一樣，如果一樣就儲存最後的時間
                            $machine_detail_now_Status = $machine_detail_old_Data;
                            $machine_detail_now_Status_Time[1] = $machine_detail['timestamp'];
                            // $machine_detail_now_Status_Time[1] = $device_data[$i]['upload_at'];//時間異常，暫時用server時間
                        } else {//如果不一樣，儲存最後的時間，並記錄到陣列中，在開始一筆新的紀錄
                            //如果判斷的是潤滑中再改變其餘皆正常，則視為相同狀態
                            if (count(array_keys(array_diff_assoc($chain_this_data, $machine_detail_old_Data))) == 1 && array_keys(array_diff_assoc($chain_this_data, $machine_detail_old_Data))[0] == 'in_lube') {
                                $machine_detail_now_Status = $machine_detail_old_Data;
                                $machine_detail_now_Status_Time[1] = $machine_detail['timestamp'];
                                // $machine_detail_now_Status_Time[1] = $device_data[$i]['upload_at'];//時間異常，暫時用server時間
                                continue;
                            }
                            $machine_detail_now_Status = $machine_detail_old_Data;
                            $machine_detail_now_Status_Time[1] = $machine_detail['timestamp'];
                            // $machine_detail_now_Status_Time[1] = $device_data[$i]['upload_at'];//時間異常，暫時用server時間
                            $machine_detail_now_Detail[count($machine_detail_now_Detail)] = $machine_detail_now_Status;
                            $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['startTime'] = $machine_detail_now_Status_Time[0];
                            $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['endTime'] = $machine_detail_now_Status_Time[1];
                            $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['cnt'] = $machine_detail['cnt'];
                         
                            $machine_detail_old_Data = $chain_this_data;
                            $machine_detail_now_Status = $machine_detail_old_Data;
                            $machine_detail_now_Status_Time = [];
                            array_push($machine_detail_now_Status_Time, $machine_detail['timestamp']);
                            // array_push($machine_detail_now_Status_Time, $device_data[$i]['upload_at']);//時間異常，暫時用server時間
                        }
                    } else {//最後一筆，儲存最後的時間，並記錄到陣列中
                        $machine_detail_now_Status = $machine_detail_old_Data;
                        $machine_detail_now_Status_Time[1] = $machine_detail['timestamp'];
                        // $machine_detail_now_Status_Time[1] = $device_data[$i]['upload_at'];//時間異常，暫時用server時間
                        $machine_detail_now_Detail[count($machine_detail_now_Detail)] = $machine_detail_now_Status;
                        $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['startTime'] = $machine_detail_now_Status_Time[0];
                        $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['endTime'] = $machine_detail_now_Status_Time[1];
                        $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['cnt'] = $machine_detail['cnt'];
                    }
                }
            }
        }
        $device_detail_data = $machine_detail_now_Detail;
    }

    return $device_detail_data;
}

//機台異常、運轉、待機時間
function Device_Status_Time($device_detail_data, $process, $machine_abn_data) {
    $machine_status_R = [];
    $OPR_count =0 ;
    if (!empty($device_detail_data) && !empty($machine_abn_data)) {
        if(count($device_detail_data) > 0) {
            if ($process == 5) {
                for ($i=0; $i < count($device_detail_data); $i++) { 
                    $status_detail = $device_detail_data[$i];
                    $err = false;
                    $machine_abn_id = [];
                    $machine_abn_description = [];
                    //判斷是否有異常
                    foreach ($machine_abn_data as $machine_abn_data_key => $machine_abn_data_value) {
                        if ($machine_abn_data_value['value'] == $status_detail[$machine_abn_data_key]) {
                            if ($machine_abn_data_key == 'in_lube') {
                                if ($status_detail['OPR'] == 1) {
                                    $err = true;
                                }
                            } else {
                                $err = true;
                            }
                        }
                    }
                    if (!$err) {
                        //判斷是否有運轉
                        if ($status_detail['OPR'] == 1) {
                            array_push($machine_status_R, array(
                                'timestamp' => [$status_detail['startTime'],$status_detail['endTime']]
                                )
                            );
                        }
                    }
                }
            } else if ($process == 6) {
                for ($i=0; $i < count($device_detail_data); $i++) { 
                    $status_detail = $device_detail_data[$i];
                    $err = false;
                    $machine_abn_id = [];
                    $machine_abn_description = [];
                    //判斷是否有異常
                    foreach ($machine_abn_data as $machine_abn_data_key => $machine_abn_data_value) {
                        if ($machine_abn_data_key != 'in_lube') {
                            if ($machine_abn_data_value['value'] == $status_detail[$machine_abn_data_key]) {
                                $err = true;
                            }
                        }
                    }
                    if (!$err) {
                        //判斷是否有運轉
                        if ($status_detail['OPR'] == 1) {
                            array_push($machine_status_R, array(
                                'timestamp' => [$status_detail['startTime'],$status_detail['endTime']]
                                )
                            );
                        }
                    }
                }
            }
        }
    }

    return [$machine_status_R];
}
