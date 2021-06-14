<?php
function MainQuery($params)//主要查詢按鈕
{
    $device_id = $params->deviceID;

    $now_date = date("Y-m-d H:i:s");//今天的日期
    // 如果日期包含今天，結束日期為今天日期
    if (strtotime($params->startTime) >= strtotime(date("Y-m-d"))) {
        if (strtotime($now_date) >= strtotime(date("Y-m-d 08:00:00"))) {
            if (strtotime($params->startTime) > strtotime(date("Y-m-d 00:00:00"))) {
                $start_date_time = date("Y-m-d 08:00:00", strtotime($params->startTime));
                $end_date_time = date("Y-m-d 08:00:00", strtotime($params->startTime));
            } else {
                $start_date_time = date("Y-m-d 08:00:00", strtotime($now_date));
                $end_date_time = $now_date;
            }
        } else if (strtotime($now_date) < strtotime(date("Y-m-d 08:00:00"))) {
            $start_date_time = date("Y-m-d 08:00:00", strtotime(date("Y-m-d 08:00:00"))-86400);
            $end_date_time = $now_date;
        }

        $cus_id = $params->cusID;
        $device = CommonSpecificKeyQuery('Redis', $cus_id . '_' . $device_id, 'no');
        if ($device['Response'] !== 'ok') {
            return;
        }
        $this_device_data = $device['QueryValueData'];

        $stack_bar_information = array($device_id => $this_device_data['stack_bar_information']);
        if (!empty($stack_bar_information[$device_id])) {
            if (is_string($stack_bar_information[$device_id])) {
                $stack_bar_information[$device_id] = json_decode($stack_bar_information[$device_id], true);
            }
        } else {
            $stack_bar_information = array($device_id => array());
            if (strtotime(date("Y-m-d H:i:s")) > strtotime(date("Y-m-d 08:00:00"))) {
                $durationTime = TimeSubtraction(date("Y-m-d 08:00:00"), date("Y-m-d H:i:s"), 'hour');
                array_push($stack_bar_information[$device_id], array(
                    'status' => null,
                    'alarmDetail' => '',
                    'startTime' =>  date("Y-m-d 08:00:00"),
                    'endTime' => date("Y-m-d H:i:s"),
                    'duration_number' => $durationTime[2]
                ));
            } else {
                $durationTime = TimeSubtraction(date("Y-m-d H:i:s", strtotime(date("Y-m-d 08:00:00")-86400)), date("Y-m-d H:i:s"), 'hour');
                array_push($stack_bar_information[$device_id], array(
                    'status' => null,
                    'alarmDetail' => '',
                    'startTime' =>  date("Y-m-d H:i:s", strtotime(date("Y-m-d 08:00:00")-86400)),
                    'endTime' => date("Y-m-d H:i:s"),
                    'duration_number' => $durationTime[2]
                ));
            }
        }

        $operatelog_information = $this_device_data['operatelog_information'];
        if (!empty($operatelog_information)) {
            if (is_string($operatelog_information)) {
                $operatelog_information = json_decode($operatelog_information, true);
            }
        } else {
            $operatelog_information = array();
            if (strtotime(date("Y-m-d H:i:s")) > strtotime(date("Y-m-d 08:00:00"))) {
                $durationTime = TimeSubtraction(date("Y-m-d 08:00:00"), date("Y-m-d H:i:s"), 'hour');
                array_push($operatelog_information, array(
                    'status' => '-',
                    'alarmCode' => '',
                    'alarmDetail' => '',
                    'startTime' => date("Y-m-d 08:00:00"),
                    'endTime' => date("Y-m-d H:i:s"),
                    'durationTime' => $durationTime[0]
                ));
            } else {
                $durationTime = TimeSubtraction(date("Y-m-d H:i:s", strtotime(date("Y-m-d 08:00:00")-86400)), date("Y-m-d H:i:s"), 'hour');
                array_push($operatelog_information, array(
                    'status' => '-',
                    'alarmCode' => '',
                    'alarmDetail' => '',
                    'startTime' => date("Y-m-d H:i:s"), strtotime(date("Y-m-d 08:00:00")-86400),
                    'endTime' => date("Y-m-d H:i:s"),
                    'durationTime' => $durationTime[0]
                ));
            }
        }
        // $Query_Device_Response = Query_Device($start_date_time, $end_date_time, isset($params->deviceID)?$params->deviceID:null, isset($params->process)?$params->process:null);
    } else {
        //因為該天的資料要到隔天才會做紀錄，所以要到隔天7點之後查詢
        $start_date_time = date("Y-m-d 08:00:00", strtotime($params->startTime) + 86400);
        $end_date_time = date("Y-m-d 08:00:00", strtotime($params->startTime) + 172800);
        if (isset($params->deviceID)) {
            $symbols = new stdClass();
            $symbols->device_id = ['equal'];
            $whereAttr = new stdClass();
            $whereAttr->device_id = [$params->deviceID];
        }
        $data = array(
            'condition_1' => array(
                'intervaltime' => array('upload_at' => array(array($start_date_time, $end_date_time))),
                'table' => 'machine_status_sum',
                'where' => isset($whereAttr)?$whereAttr:'',
                'limit' => ['ALL'],
                'symbols' => isset($symbols)?$symbols:''
            )
        );
        
        $machine_status_sum = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
        if ($machine_status_sum['Response'] !== 'ok') {
            return $machine_status_sum;
        } else if (count($machine_status_sum['QueryTableData']) == 0) {
            $machine_status_sum['Response'] = "no data";
        }
        $Query_Device_Response = $machine_status_sum['QueryTableData'];
    };

    $operatelog_data = array('total_data'=>[], 'machine_data'=>[]);
    if(!empty($Query_Device_Response)) {
        for ($i=0; $i < count($Query_Device_Response); $i++) { 
            $device_id = $Query_Device_Response[$i]['device_id'];
            if (!isset($operatelog_data['machine_data'][$device_id])) {
                $operatelog_data['machine_data'][$device_id] = [];
            }
            foreach ($Query_Device_Response[$i]['machine_detail'] as $status => $value) {
                // echo json_encode($value['datail']);
                foreach ($value['datail'] as $datail) {
                    $startTime = date("Y-m-d H:i:s",strtotime($datail['timestamp'][0]));
                    $endTime = date("Y-m-d H:i:s",strtotime($datail['timestamp'][1]));
                    $durationTime = TimeSubtraction($startTime, $endTime, 'hour');
                    if (isset($datail['machine_abn_id'])) {
                        if (empty(strpos($datail['machine_abn_id'], ','))) {
                            $datail['machine_abn_id'] = array($datail['machine_abn_id']);
                            $datail['machine_abn_description'] = array($datail['machine_abn_description']);
                        } else {
                            $datail['machine_abn_id'] = explode(",", $datail['machine_abn_id']);
                            $datail['machine_abn_description'] = explode(",", $datail['machine_abn_description']);
                        }
                    }
                    array_push($operatelog_data['total_data'], array(
                        'device_id' => $device_id,
                        'place_item' => '二廠',
                        'group_item' => '組別',
                        'class_item' => '日班',
                        'status' => $status == 'S' ? '關機' : ($status == 'H' ? '警報' : ($status == 'R' ? '生產' : ($status == 'Q' ? '待機' : ''))),
                        'alarmCode' => isset($datail['machine_abn_id'])?implode("\n",$datail['machine_abn_id']):'',
                        'alarmDetail' => isset($datail['machine_abn_description'])?implode("\n",$datail['machine_abn_description']):'',
                        'startTime' =>  $startTime,
                        'endTime' => $endTime,
                        'durationTime' => $durationTime[0]
                    ));
                    array_push($operatelog_data['machine_data'][$device_id], array(
                        'status' => $status == 'S' ? '關機' : ($status == 'H' ? '警報' : ($status == 'R' ? '生產' : ($status == 'Q' ? '待機' : ''))),
                        // 'alarmCode' => isset($datail['machine_abn_id'])?implode("\n",$datail['machine_abn_id']):'',
                        'alarmDetail' => isset($datail['machine_abn_description'])?implode("\n",$datail['machine_abn_description']):'',
                        'startTime' =>  $startTime,
                        'endTime' => $endTime,
                        'duration_number' => $durationTime[2]
                    ));
                }
                usort($operatelog_data['machine_data'][$device_id], 'sort_start_time');
                usort($operatelog_data['total_data'], 'sort_start_time');
            }
            if (count($operatelog_data['machine_data'][$device_id]) > 0) {
                if ($operatelog_data['machine_data'][$device_id][count($operatelog_data['machine_data'][$device_id])-1]['status'] == '關機' && $operatelog_data['machine_data'][$device_id][count($operatelog_data['machine_data'][$device_id])-1]['duration_number'] < 60) {
                    array_pop($operatelog_data['total_data']);
                    array_pop($operatelog_data['machine_data'][$device_id]);
                }
            } else {
                $startTime = $time_interval['start'];
                $endTime = date("Y-m-d H:i:s", $now_time);
                $durationTime = TimeSubtraction($startTime, $endTime, 'hour');
                array_push($operatelog_data['total_data'], array(
                    'device_id' => $device_id,
                    'place_item' => '二廠',
                    'group_item' => '組別',
                    'class_item' => '日班',
                    'status' => '關機',
                    'alarmCode' => '',
                    'alarmDetail' => '',
                    'startTime' =>  $startTime,
                    'endTime' => $endTime,
                    'durationTime' => $durationTime[0]
                ));
                array_push($operatelog_data['machine_data'][$device_id], array(
                    'status' => '關機',
                    'alarmDetail' => '',
                    'startTime' =>  $startTime,
                    'endTime' => $endTime,
                    'duration_number' => $durationTime[2]
                ));
            }
        }
    } else if (isset($stack_bar_information) && isset($operatelog_information)) {
        $operatelog_data['total_data'] = $operatelog_information;
        $operatelog_data['machine_data'] = $stack_bar_information;
    } else {
        $returnData['Response'] = 'no data';
        return $returnData;
    }
    //排序
    usort($operatelog_data['total_data'], 'sort_start_time');

    $returnData['QueryTableData'] = [$operatelog_data];
    // $returnData['test'] = $test;
    $returnData['Response'] = 'ok';

    return $returnData;
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

    //查詢machine_on_off_hist，查詢所有機台今日的開關機狀態
    $machine_on_off_hist_data = Query_All_Device_On_Off($previous_time, $now_time, $select_device_name);

    // //查詢work_code_use，查詢所有機台今日上下線的工單
    // $work_code_use_data = Query_All_Device_Work_Code($previous_time, $now_time, $select_device_name);

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
            //紀錄停機時間
            $machine_status_S = Device_Stop_Time($device_name, isset($machine_on_off_hist_data[$device_name])?$machine_on_off_hist_data[$device_name]:null, $previous_time, $now_time);
            //加總停機時間
            [$machine_status_S_time_rate, $machine_status_S_time_array] = Device_All_Time($machine_status_S, $totalTime);

            //整理出停機以外的時間資料
            $device_detail_time_data = Device_Detail_Time($device_name, $device_detail_data, $machine_status_S, $previous_time, $now_time);

            //整理出異常、運轉、待機時間
            [$machine_status_H, $machine_status_R, $machine_status_Q] = Device_Status_Time($device_name, $device_detail_time_data, $process, $machine_light_abn_data[$device_name], $machine_status_S, $previous_time, $now_time);
            //加總異常時間
            [$machine_status_H_time_rate, $machine_status_H_time_array] = Device_All_Time($machine_status_H, $totalTime);
            [$machine_status_R_time_rate, $machine_status_R_time_array] = Device_All_Time($machine_status_R, $totalTime);
            [$machine_status_Q_time_rate, $machine_status_Q_time_array] = Device_All_Time($machine_status_Q, $totalTime);

            // // 取得機台運轉時所加工的工單
            // $machine_status_R = Device_Run_Work_Code($device_name, $machine_status_R,  isset($work_code_use_data[$device_name])?$work_code_use_data[$device_name]:[], $previous_time, $now_time);

            $all_time_array = array_merge($machine_status_S_time_array, $machine_status_H_time_array, $machine_status_R_time_array, $machine_status_Q_time_array);

            //將剩餘的時間加入停機時間
            $machine_status_S = array_merge($machine_status_S, Device_Remaining_Time($all_time_array, $previous_time, $now_time));

            //排序停機時間
            usort($machine_status_S, 'sort_timestamp_first_time');
            //確認停機時間無交集
            if (count($machine_status_S) > 1) {
                $machine_status_S = Check_Time_No_Cross($machine_status_S);
            }
            //加總停機時間
            [$machine_status_S_time_rate, $machine_status_S_time_array] = Device_All_Time($machine_status_S, $totalTime);

            //儲存
            $machine_status[$device_name] = array(
                'S' => array(
                    'rate' => $machine_status_S_time_rate . '%',
                    'datail' => $machine_status_S
                ),
                'H' => array(
                    'rate' => $machine_status_H_time_rate . '%',
                    'datail' => $machine_status_H
                ),
                'R' => array(
                    'rate' => $machine_status_R_time_rate . '%',
                    'datail' => $machine_status_R
                ),
                'Q' => array(
                    'rate' => $machine_status_Q_time_rate . '%',
                    'datail' => $machine_status_Q
                )
            );
        } else {
            $machine_status[$device_name] = array(
                'S' => array(
                    'rate' => '100%',
                    'datail' => [array('timestamp' => [$previous_time, $now_time])]
                ),
                'H' => array(
                    'rate' => '0%',
                    'datail' => []
                ),
                'R' => array(
                    'rate' => '0%',
                    'datail' => []
                ),
                'Q' => array(
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

//查詢machine_on_off_hist，查詢所有機台今日的開關機狀態
function Query_All_Device_On_Off($previous_time, $now_time, $select_device_name) {
    if (isset($select_device_name)) {
        $symbols = new stdClass();
        $symbols->device_name = ['equal'];
        $whereAttr = new stdClass();
        $whereAttr->device_name = [strtolower($select_device_name)];
    }
    $data = array(
        'condition_1' => array(
            'intervaltime' => array('upload_at' => array(array($previous_time, $now_time))),
            'table' => 'machine_on_off_hist',
            'where' => isset($whereAttr)?$whereAttr:'',
            'limit' => ['ALL'],
            'symbols' => isset($symbols)?$symbols:''
        )
    );
    
    $machine_on_off_hist = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    if ($machine_on_off_hist['Response'] != 'ok' || count($machine_on_off_hist['QueryTableData']) == 0) {//先抓是否抓取成功，成功的話繼續執行
        return [];
    } else {
        $machine_on_off_hist = $machine_on_off_hist['QueryTableData'];
    }
    
    for ($i=0; $i < count($machine_on_off_hist); $i++) { 
        $device_name = strtoupper($machine_on_off_hist[$i]['device_name']);
        if (!isset($machine_on_off_hist_data[$device_name])) {
            $machine_on_off_hist_data[$device_name] = [];
        }
        array_push($machine_on_off_hist_data[$device_name], $machine_on_off_hist[$i]);
    }

    return $machine_on_off_hist_data;
}

// //查詢work_code_use，查詢所有機台今日上下線的工單
// function Query_All_Device_Work_Code($previous_time, $now_time) {
//     $data = array(
//         'col' => 'upload_at',
//         'valueStart' => $previous_time,
//         'valueEnd' => $now_time
//     );
//     $work_code_use = CommonIntervalQuery($data, "PostgreSQL", strtolower($work_code_use));
//     if ($work_code_use['Response'] != 'ok' || count($work_code_use['QueryTableData']) == 0) {//先抓是否抓取成功，成功的話繼續執行
//         return [];
//     } else {
//         $work_code_use = $work_code_use['QueryTableData'];
//     }
    
//     for ($i=0; $i < count($work_code_use); $i++) { 
//         $device_name = $work_code_use[$i]['device_name'];
//         if (!isset($work_code_use_data[$device_name])) {
//             $work_code_use_data[$device_name] = [];
//         }
//         array_push($work_code_use_data[$device_name], $work_code_use[$i]);
//     }

//     return $work_code_use_data;
// }

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

//機台停機時間
function Device_Stop_Time($device_name, $machine_on_off_hist_data, $previous_time, $now_time) {
    $machine_status_S = [];
    if (!empty($machine_on_off_hist_data)) {
        for ($i=0; $i < count($machine_on_off_hist_data); $i++) { 
            if (empty($machine_status_S)) {
                if ($machine_on_off_hist_data[$i]['status'] == 'S') {
                    if (strtotime($previous_time) == strtotime($machine_on_off_hist_data[$i]['upload_at']) && count($machine_on_off_hist_data) == 1) {
                        return $machine_status_S = [];
                    }
                    array_push($machine_status_S, array(
                        'timestamp' => [$previous_time, $machine_on_off_hist_data[$i]['upload_at']]
                        )
                    );
                    continue;
                }
            }
            if ($machine_on_off_hist_data[$i]['status'] == 'E') {
                array_push($machine_status_S, array(
                    'timestamp' => [$machine_on_off_hist_data[$i]['upload_at']]
                    )
                );
            } else if ($machine_on_off_hist_data[$i]['status'] == 'S') {
                $position = count($machine_status_S) - 1;
                array_push($machine_status_S[$position]['timestamp'], $machine_on_off_hist_data[$i]['upload_at']);
            }
        }
    } else {
        $symbols = new stdClass();
        $symbols->device_name = ["equal"];
        $whereAttr = new stdClass();
        $whereAttr->device_name = [strtolower($device_name)];
        $data = array(
            'condition_1' => array(
                'table' => 'machine_on_off_hist',
                'limit' => [0,1],
                'orderby' => ['desc', 'upload_at'],
                'where' => $whereAttr,
                'symbols' => $symbols
            )
        );
        $this_machine_on_off_hist = CommonSqlSyntax_Query($data, 'PostgreSQL');
        if ($this_machine_on_off_hist['Response'] != 'ok' || count($this_machine_on_off_hist['QueryTableData']) == 0) {//先抓是否抓取成功，成功的話繼續執行
            $this_machine_on_off_hist_data = [];
        } else {
            $this_machine_on_off_hist_data = $this_machine_on_off_hist['QueryTableData'];
        }

        if (!empty($this_machine_on_off_hist_data)) {
            if ($machine_on_off_hist_data[0]['status'] == 'E') {
                array_push($machine_status_S,  array(
                    'timestamp' => [$previous_time, $now_time]
                    )
                );
            }
        }
    }
    if (!empty($machine_status_S)) {
        $machine_status_S_length = count($machine_status_S);
        if (count($machine_status_S[$machine_status_S_length - 1]['timestamp']) != 2) {
            array_push($machine_status_S[$machine_status_S_length - 1]['timestamp'], $now_time);
        }
    }

    return $machine_status_S;
}

//停機以外的時間
function Device_Detail_Time($device_name, $device_detail_data, $machine_status_S, $previous_time, $now_time) {
    
    $device_detail_time_data = [];
    if (!empty($device_detail_data)) {
        if(count($device_detail_data) > 0) {
            for ($i=0; $i < count($device_detail_data); $i++) { 
                $status_detail = $device_detail_data[$i];

                $device_time_start = strtotime($status_detail['startTime']);
                $device_time_end = strtotime($status_detail['endTime']);
                for ($j=0; $j < count($machine_status_S); $j++) { 
                    $stop_time_start = strtotime($machine_status_S[$j]['timestamp'][0]);
                    $stop_time_end = strtotime($machine_status_S[$j]['timestamp'][1]);
                    if ($stop_time_start < $device_time_start && $stop_time_end < $device_time_start && $stop_time_start < $device_time_end && $stop_time_end < $device_time_end) {

                    } else if ($stop_time_start <= $device_time_start && $stop_time_end < $device_time_start && $stop_time_start > $device_time_end && $stop_time_end < $device_time_end) {
                        $status_detail['startTime'] = $machine_status_S[$j]['timestamp'][1];
                    } else if ($stop_time_start <= $device_time_start && $stop_time_end <= $device_time_start && $stop_time_start >= $device_time_end && $stop_time_end >= $device_time_end) {
                        $status_detail['startTime'] = '1970-01-01 08:00:00';
                        $status_detail['endTime'] = '1970-01-01 08:00:00';
                    } else if ($stop_time_start >= $device_time_start && $stop_time_end <= $device_time_start && $stop_time_start >= $device_time_end && $stop_time_end <= $device_time_end) {
                        array_splice($device_detail_data, $i + 1, 0, array(
                            $status_detail)
                        );
                        $device_detail_data[$i + 1]['startTime'] = $machine_status_S[$j]['timestamp'][1];
                        $status_detail['endTime'] = $machine_status_S[$j]['timestamp'][0];
                    break;
                    } else if ($stop_time_start > $device_time_start && $stop_time_end < $device_time_start && $stop_time_start > $device_time_end && $stop_time_end >= $device_time_end) {
                        $status_detail['endTime'] = $machine_status_S[$j]['timestamp'][0];
                    } else if ($stop_time_start > $device_time_start && $stop_time_end > $device_time_start && $stop_time_start > $device_time_end && $stop_time_end > $device_time_end) {

                    } else if ($stop_time_start > $device_time_start && $stop_time_end >= $device_time_start && $stop_time_start <= $device_time_end && $stop_time_end <= $device_time_end) {
                        array_splice($device_detail_data, $i + 1, 0, array(
                            $status_detail)
                        );
                        $device_detail_data[$i + 1]['startTime'] = $machine_status_S[$j]['timestamp'][1];
                        $status_detail['endTime'] = $machine_status_S[$j]['timestamp'][0];
                    break;
                    } else if ($stop_time_start <= $device_time_start && $stop_time_end >= $device_time_start && $stop_time_start < $device_time_end && $stop_time_end < $device_time_end) {
                        $status_detail['startTime'] = $machine_status_S[$j]['timestamp'][1];
                    } else if ($stop_time_start <= $device_time_start && $stop_time_end >= $device_time_start && $stop_time_start < $device_time_end && $stop_time_end > $device_time_end) {
                        $status_detail['startTime'] = '1970-01-01 08:00:00';
                        $status_detail['endTime'] = '1970-01-01 08:00:00';
                    } else if ($stop_time_start > $device_time_start && $stop_time_end > $device_time_start && $stop_time_start <= $device_time_end && $stop_time_end > $device_time_end) {
                        $status_detail['endTime'] = $machine_status_S[$j]['timestamp'][0];
                    }
                }
                array_push($device_detail_time_data, $status_detail);
            }
            $remove_array = array_keys(array_column($device_detail_time_data, 'startTime'), '1970-01-01 08:00:00');
            if (!empty($remove_array)) {
                foreach ($remove_array as $key) {
                    unset($device_detail_time_data[$key]);
                };
            };
        }
    }
    
    return array_values($device_detail_time_data);
}

//機台異常、運轉、待機時間
function Device_Status_Time($device_name, $device_detail_data, $process, $machine_light_abn_data, $machine_status_S, $previous_time, $now_time) {
    $machine_status_H = [];
    $machine_status_R = [];
    $machine_status_Q = [];
    $OPR_count =0 ;
    if (!empty($device_detail_data) && !empty($machine_light_abn_data)) {
        if(count($device_detail_data) > 0) {
            if ($process == 5) {
                for ($i=0; $i < count($device_detail_data); $i++) { 
                    $status_detail = $device_detail_data[$i];
                    $machine_abn_id = [];
                    $machine_abn_description = [];
                    //判斷是否有異常
                    foreach ($machine_light_abn_data as $machine_light_abn_data_key => $machine_light_abn_data_key_value) {
                        if ($machine_light_abn_data_key_value['value'] == $status_detail[$machine_light_abn_data_key]) {
                            if ($machine_light_abn_data_key == 'in_lube') {
                                if ($status_detail['OPR'] == 1) {
                                    $status_detail['err_data'] = true;
                                    array_push($machine_abn_id, $machine_light_abn_data_key_value['err_code']);
                                    array_push($machine_abn_description, $machine_light_abn_data_key_value['description']);
                                }
                            } else {
                                $status_detail['err_data'] = true;
                                array_push($machine_abn_id, $machine_light_abn_data_key_value['err_code']);
                                array_push($machine_abn_description, $machine_light_abn_data_key_value['description']);
                            }
                            // $status_detail['err_data'] = true;
                            // array_push($machine_abn_id, $machine_light_abn_data_key_value['err_code']);
                            // array_push($machine_abn_description, $machine_light_abn_data_key_value['description']);
                        }
                    }
                    if ($i == 0) {
                        $first_time = '';
                        if (count($machine_status_S) > 0) {
                            if ($machine_status_S[0]['timestamp'][0] == $previous_time && strtotime($machine_status_S[0]['timestamp'][0]) >= strtotime($previous_time)) {
                                $first_time = $machine_status_S[0]['timestamp'][1];
                            }
                        } 
                        if (!empty($machine_abn_id)) {
                            array_push($machine_status_H, array(
                                'machine_abn_id' => $machine_abn_id,
                                'machine_abn_description' => $machine_abn_description,
                                'timestamp' => [$first_time != '' ? $first_time : $previous_time,$status_detail['endTime']]
                                )
                            );
                        } else {
                            //判斷是否有運轉
                            if ($status_detail['OPR'] == 1) {
                                array_push($machine_status_R, array(
                                    'timestamp' => [$first_time != '' ? $first_time : $previous_time,$status_detail['endTime']]
                                    )
                                );
                            } else {
                                array_push($machine_status_Q, array(
                                    'timestamp' => [$first_time != '' ? $first_time : $previous_time,$status_detail['endTime']]
                                    )
                                );
                            }
                        }
                    } else {
                        if (!empty($machine_abn_id)) {
                            array_push($machine_status_H, array(
                                'machine_abn_id' => $machine_abn_id,
                                'machine_abn_description' => $machine_abn_description,
                                'timestamp' => [$status_detail['startTime'],$status_detail['endTime']]
                                )
                            );
                        } else {
                            //判斷是否有運轉
                            if ($status_detail['OPR'] == 1) {
                                array_push($machine_status_R, array(
                                    'timestamp' => [$status_detail['startTime'],$status_detail['endTime']]
                                    )
                                );
                            } else {
                                array_push($machine_status_Q, array(
                                    'timestamp' => [$status_detail['startTime'],$status_detail['endTime']]
                                    )
                                );
                            }
                        }
                    }
                }
            } else if ($process == 6) {
                for ($i=0; $i < count($device_detail_data); $i++) { 
                    $status_detail = $device_detail_data[$i];
                    $machine_abn_id = [];
                    $machine_abn_description = [];
                    //判斷是否有異常
                    foreach ($machine_light_abn_data as $machine_light_abn_data_key => $machine_light_abn_data_key_value) {
                        if ($machine_light_abn_data_key != 'in_lube') {
                            if ($machine_light_abn_data_key_value['value'] == $status_detail[$machine_light_abn_data_key]) {
                                $status_detail['err_data'] = true;
                                array_push($machine_abn_id, $machine_light_abn_data_key_value['err_code']);
                                array_push($machine_abn_description, $machine_light_abn_data_key_value['description']);
                            }
                        }
                    }
                    if ($i == 0) {
                        $first_time = '';
                        if (count($machine_status_S) > 0) {
                            if ($machine_status_S[0]['timestamp'][0] == $previous_time && strtotime($machine_status_S[0]['timestamp'][0]) >= strtotime($previous_time)) {
                                $first_time = $machine_status_S[0]['timestamp'][1];
                            }
                        } 
                        if (!empty($machine_abn_id)) {
                            array_push($machine_status_H, array(
                                'machine_abn_id' => $machine_abn_id,
                                'machine_abn_description' => $machine_abn_description,
                                'timestamp' => [$first_time != '' ? $first_time : $previous_time,$status_detail['endTime']]
                                )
                            );
                        } else {
                            //判斷是否有運轉
                            if ($status_detail['OPR'] == 1) {
                                array_push($machine_status_R, array(
                                    'timestamp' => [$first_time != '' ? $first_time : $previous_time,$status_detail['endTime']]
                                    )
                                );
                            } else {
                                array_push($machine_status_Q, array(
                                    'timestamp' => [$first_time != '' ? $first_time : $previous_time,$status_detail['endTime']]
                                    )
                                );
                            }
                        }
                    } else {
                        if (!empty($machine_abn_id)) {
                            array_push($machine_status_H, array(
                                'machine_abn_id' => $machine_abn_id,
                                'machine_abn_description' => $machine_abn_description,
                                'timestamp' => [$status_detail['startTime'],$status_detail['endTime']]
                                )
                            );
                        } else {
                            //判斷是否有運轉
                            if ($status_detail['OPR'] == 1) {
                                array_push($machine_status_R, array(
                                    'timestamp' => [$status_detail['startTime'],$status_detail['endTime']]
                                    )
                                );
                            } else {
                                array_push($machine_status_Q, array(
                                    'timestamp' => [$status_detail['startTime'],$status_detail['endTime']]
                                    )
                                );
                            }
                        }
                    }
                }
            }
        }
    }

    return [$machine_status_H, $machine_status_R, $machine_status_Q];
}

//補足機台剩餘不足1天的時間
function Device_Remaining_Time($all_time_array, $previous_time, $now_time) {
    // 排序時間
    usort($all_time_array, 'sort_first_time');
    $machine_status_S = [array(
        'timestamp' => [$previous_time, $now_time]
    )];
    for ($i=0; $i < count($all_time_array); $i++) { 
        $all_time_array_start = strtotime($all_time_array[$i][0]);
        $all_time_array_end = strtotime($all_time_array[$i][1]);

        for ($j=0; $j < count($machine_status_S); $j++) { 
            $queue_time_start = strtotime($machine_status_S[$j]['timestamp'][0]);
            $queue_time_end = strtotime($machine_status_S[$j]['timestamp'][1]);
            if ($all_time_array_start < $queue_time_start && $all_time_array_start < $queue_time_end && $all_time_array_end < $queue_time_start && $all_time_array_end < $queue_time_end) {

            } else if ($all_time_array_start <= $queue_time_start && $all_time_array_start < $queue_time_end && $all_time_array_end > $queue_time_start && $all_time_array_end < $queue_time_end) {
                $machine_status_S[$j]['timestamp'][0] = $all_time_array[$i][1];
            } else if ($all_time_array_start <= $queue_time_start && $all_time_array_start <= $queue_time_end && $all_time_array_end >= $queue_time_start && $all_time_array_end >= $queue_time_end) {
                $machine_status_S[$j]['timestamp'][0] = '1970-01-01 08:00:00';
                $machine_status_S[$j]['timestamp'][1] = '1970-01-01 08:00:00';
            } else if ($all_time_array_start > $queue_time_start && $all_time_array_start <= $queue_time_end && $all_time_array_end >= $queue_time_start && $all_time_array_end <= $queue_time_end) {
                array_splice($machine_status_S, $j + 1, 0, array(array('timestamp' => [$all_time_array[$i][1], $machine_status_S[$j]['timestamp'][1]])));
                $machine_status_S[$j]['timestamp'][1] = $all_time_array[$i][0];
            } else if ($all_time_array_start > $queue_time_start && $all_time_array_start < $queue_time_end && $all_time_array_end > $queue_time_start && $all_time_array_end >= $queue_time_end) {
                $machine_status_S[$j]['timestamp'][1] = $all_time_array[$i][0];
            } else if ($all_time_array_start > $queue_time_start && $all_time_array_start > $queue_time_end && $all_time_array_end >= $queue_time_start && $all_time_array_end > $queue_time_end) {

            }
        }
        $remove_array = array_keys(array_column($machine_status_S, 'timestamp'), ['1970-01-01 08:00:00','1970-01-01 08:00:00']);
        if (!empty($remove_array)) {
            foreach ($remove_array as $key) {
                unset($machine_status_S[$key]);
            };
        };
    }
    return $machine_status_S;
}

//將重疊在一起的時間合併
function Check_Time_No_Cross($machine_status_detail) {
    $new_machine_status_detail = [];
    for ($i=0; $i < count($machine_status_detail) - 1; $i++) { 
        if (strtotime($machine_status_detail[$i]['timestamp'][1]) == strtotime($machine_status_detail[$i + 1]['timestamp'][0])) {
            array_push($new_machine_status_detail, array('timestamp'=>[$machine_status_detail[$i]['timestamp'][0], $machine_status_detail[$i + 1]['timestamp'][1]]));
            $i++;
        } else {
            array_push($new_machine_status_detail, $machine_status_detail[$i]);
            if ($i == count($machine_status_detail) - 2) {
                array_push($new_machine_status_detail, $machine_status_detail[$i + 1]);
            }
        }
    }
    return $new_machine_status_detail;
}

//陣列裡的timestamp的第一個元素排序
function sort_timestamp_first_time($a, $b){
    if(strtotime($a['timestamp'][0]) == strtotime($b['timestamp'][0])) return 0;
    return (strtotime($a['timestamp'][0]) > strtotime($b['timestamp'][0])) ? 1 : -1;
}

//機台時間
function Device_All_Time($machine_status, $totalTime){
    $time = 0;
    $time_array = [];
    foreach ($machine_status as $key => $value) {
        $time += (strtotime($value['timestamp'][1]) - strtotime($value['timestamp'][0]));
        array_push($time_array, $value['timestamp']);
    }
    $time = round(round($time / $totalTime, 2) * 100);
    return [$time, $time_array];
}

//陣列裡的第一個元素排序
function sort_first_time($a, $b){
    if(strtotime($a[0]) == strtotime($b[0])) return 0;
    return (strtotime($a[0]) > strtotime($b[0])) ? 1 : -1;
}
//陣列裡的第一個元素排序
function sort_start_time($a, $b){
    if(strtotime($a['startTime']) == strtotime($b['startTime'])) return 0;
    return (strtotime($a['startTime']) > strtotime($b['startTime'])) ? 1 : -1;
}

//判斷是否有交集
function is_time_cross($source_begin_time_1 = '', $source_end_time_1 = '', $source_begin_time_2 = '', $source_end_time_2 = '') {
    $beginTime1 = strtotime($source_begin_time_1);
    $endTime1 = strtotime($source_end_time_1);
    $beginTime2 = strtotime($source_begin_time_2);
    $endTime2 = strtotime($source_end_time_2);
    $status = $beginTime2 - $beginTime1;
    if ($status > 0) {
        $status2 = $beginTime2 - $endTime1;
        if ($status2 >= 0) {
            return false;
        } else {
            return true;
        }
    } else {
        $status2 = $endTime2 - $beginTime1;
        if ($status2 > 0) {
            return true;
        } else {
            return false;
        }
    }
}