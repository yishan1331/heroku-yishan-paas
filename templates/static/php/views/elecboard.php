<?php
function MainQuery($params) //主要查詢按鈕
{
    //回傳的資料
    $returnData['QueryTableData'] = [];
    $cus_id = $params->cusID;
    //查詢所有機台
    $device = CommonSpecificKeyQuery('Redis', $cus_id . '*', 'yes');
    if ($device['Response'] !== 'ok') {
        $returnData['Response'] = 'no data';
        $returnData['page'] = 'elecboard';
        return $returnData;
    }
    $device_data = $device['QueryValueData'];

    $category = $params->category;

    $device_back_data = array();
    foreach ($device_data as $key => $value) {
        if ($value['device_category'] == $category) {
            $device_id = $value['device_id'];
            $device_name = $value['device_name'];
            if (empty($value['machine_status']) || $value['machine_status'] == 'S') {
                $machine_status = '-';
            } else if ($value['machine_status'] == 'Q') {
                $machine_status = '待機';
            } else if ($value['machine_status'] == 'R') {
                $machine_status = '運作';
            } else if ($value['machine_status'] == 'H') {
                $machine_status = '異常';
            }
            $rpm = $value['device_rpm'];
            $stack_bar_information = array($device_name => $value['stack_bar_information']);
            if (!empty($stack_bar_information[$device_name])) {
                if (is_string($stack_bar_information[$device_name])) {
                    $stack_bar_information[$device_name] = json_decode($stack_bar_information[$device_name], true);
                }
            } else {
                $stack_bar_information = array($device_name => array());
                if (strtotime(date("Y-m-d H:i:s")) > strtotime(date("Y-m-d 08:00:00"))) {
                    $durationTime = TimeSubtraction(date("Y-m-d 08:00:00"), date("Y-m-d H:i:s"), 'hour');
                    array_push($stack_bar_information[$device_name], array(
                        'status' => null,
                        'alarmDetail' => '',
                        'startTime' =>  date("Y-m-d 08:00:00"),
                        'endTime' => date("Y-m-d H:i:s"),
                        'duration_number' => $durationTime[2]
                    ));
                } else {
                    $durationTime = TimeSubtraction(date("Y-m-d H:i:s", strtotime(date("Y-m-d 08:00:00")-86400)), date("Y-m-d H:i:s"), 'hour');
                    array_push($stack_bar_information[$device_name], array(
                        'status' => null,
                        'alarmDetail' => '',
                        'startTime' =>  date("Y-m-d H:i:s", strtotime(date("Y-m-d 08:00:00")-86400)),
                        'endTime' => date("Y-m-d H:i:s"),
                        'duration_number' => $durationTime[2]
                    ));
                }
            }
            $stack_bar_information[$device_name][0]['stacksBarNumber'] = array("08","09","10","11","12","13","14","15","16","17","18","19","20","21","22","23","00","01","02","03","04","05","06","07","08");
            array_push($device_back_data, array(
                'device_id' => $device_id,
                'device_name' => $device_name,
                'category' => $category,
                'machine_status' => $machine_status,
                'rpm' => $rpm,
                'device_stackBar' => $stack_bar_information
            ));
        }
    }
    usort($device_back_data, 'sort_device');
    $returnData['QueryTableData'] = $device_back_data;
    $returnData['Response'] = 'ok';
    $returnData['page'] = 'elecboard';
    return $returnData;
}

function SingleQuery($params) //單機台查詢按鈕
{
    //回傳的資料
    $returnData['QueryTableData'] = [];
    
    $cus_id = $params->cusID;
    $device_id = $params->deviceID;

    //查詢所有機台
    $device = CommonSpecificKeyQuery('Redis', $cus_id . '_' . $device_id, 'no');
    if ($device['Response'] !== 'ok') {
        $returnData['Response'] = 'no data';
        $returnData['page'] = 'elecboard';
        return $returnData;
    }
    $this_device_data = $device['QueryValueData'];

    $device_back_data = array();

    $device_id = $this_device_data['device_id'];
    $device_name = $this_device_data['device_name'];
    $device_model = $this_device_data['device_model'];
    $category = $this_device_data['device_category'];
    $machine_image = $this_device_data['machine_image'];
    if (empty($this_device_data['machine_status'])) {
        $machine_status = 'S';
    } else {
        $machine_status = $this_device_data['machine_status'];
    }
    $device_run_time = $this_device_data['device_run_time'];
    $device_activation = $this_device_data['device_activation'];
    $rpm = $this_device_data['device_rpm'];
    $device_day_start_count = $this_device_data['device_day_start_count'];
    $device_day_count = $this_device_data['device_day_count'];
    $device_day_count = (int)$device_day_count - (int)$device_day_start_count;
    $device_now_count = $this_device_data['device_now_count'];
    $wire_weight = $this_device_data['wire_weight'];

    $stack_bar_information = array($device_name => $this_device_data['stack_bar_information']);
    if (!empty($stack_bar_information[$device_name])) {
        if (is_string($stack_bar_information[$device_name])) {
            $stack_bar_information[$device_name] = json_decode($stack_bar_information[$device_name], true);
        }
    } else {
        $stack_bar_information = array($device_name => array());
        if (strtotime(date("Y-m-d H:i:s")) > strtotime(date("Y-m-d 08:00:00"))) {
            $durationTime = TimeSubtraction(date("Y-m-d 08:00:00"), date("Y-m-d H:i:s"), 'hour');
            array_push($stack_bar_information[$device_name], array(
                'status' => null,
                'alarmDetail' => '',
                'startTime' =>  date("Y-m-d 08:00:00"),
                'endTime' => date("Y-m-d H:i:s"),
                'duration_number' => $durationTime[2]
            ));
        } else {
            $durationTime = TimeSubtraction(date("Y-m-d H:i:s", strtotime(date("Y-m-d 08:00:00")-86400)), date("Y-m-d H:i:s"), 'hour');
            array_push($stack_bar_information[$device_name], array(
                'status' => null,
                'alarmDetail' => '',
                'startTime' =>  date("Y-m-d H:i:s", strtotime(date("Y-m-d 08:00:00")-86400)),
                'endTime' => date("Y-m-d H:i:s"),
                'duration_number' => $durationTime[2]
            ));
        }
    }
    $stack_bar_information[$device_name][0]['stacksBarNumber'] = array("08","09","10","11","12","13","14","15","16","17","18","19","20","21","22","23","00","01","02","03","04","05","06","07","08");

    $machine_camera = $this_device_data['machine_camera'];
    if (!empty($machine_camera)) {
        if (is_string($machine_camera)) {
            $machine_camera = json_decode($machine_camera, true);
        }
    }

    $error_level = $this_device_data['error_level'];
    if (!empty($error_level)) {
        if (is_string($error_level)) {
            $error_level = json_decode($error_level, true);
        }
    }
    
    $operatelog_information = $this_device_data['operatelog_information'];
    if (!empty($operatelog_information)) {
        $alarmHistory_information = array();
        if (is_string($operatelog_information)) {
            $operatelog_information = json_decode($operatelog_information, true);
        }
        foreach ($operatelog_information as $key => $value) {
            if ($value['status'] == '警報') {
                $machine_abn_id_array = explode("\n", $value['alarmCode']);
                $alarmLevel = '-';
                $max_level = 0;
                foreach ($machine_abn_id_array as $machine_abn_id_key => $machine_abn_id_value) {
                    if (empty(strpos($machine_abn_id_value, '0_'))) {
                        $this_level = explode('_', $machine_abn_id_value)[0];
                        if ($max_level < $this_level) {
                            $max_level = $this_level;
                        }
                    }
                }
                if ($max_level != 0) {
                    if (isset($error_level[$max_level])) {
                        $alarmLevel = $error_level[$max_level];
                    }

                    array_push($alarmHistory_information, array(
                        'alarmLevel' => $alarmLevel,
                        'alarmDetail' => $value['alarmDetail'],
                        'alarmCode' => $value['alarmCode'],
                        'alarmVideo' => $value['alarmVideo'],
                        'startTime' => $value['startTime'],
                        'endTime' => $value['endTime'],
                        'continuousTime' => $value['durationTime']
                    ));
                }
            }
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
            $durationTime = TimeSubtraction(date("Y-m-d H:i:s", strtotime(date("Y-m-d 08:00:00") - 86400)), date("Y-m-d H:i:s"), 'hour');
            array_push($operatelog_information, array(
                'status' => '-',
                'alarmCode' => '',
                'alarmDetail' => '',
                'startTime' => date("Y-m-d H:i:s"), strtotime(date("Y-m-d 08:00:00") - 86400),
                'endTime' => date("Y-m-d H:i:s"),
                'durationTime' => $durationTime[0]
            ));
        }
        $alarmHistory_information = array();
    }
    
    $machine_light_value = $this_device_data['machine_light_value'];
    if (!empty($machine_light_value)) {
        if (is_string($machine_light_value)) {
            $machine_light_value = json_decode($machine_light_value, true);
        }
    }

    $diagnosis_message = $this_device_data['diagnosis_message'];
    if (!empty($diagnosis_message)) {
        if (is_string($diagnosis_message)) {
            $diagnosis_message = json_decode($diagnosis_message, true);
        }
    }
    
    $machine_abn_id = $this_device_data['machine_abn_id'];
    $machine_abn_description = $this_device_data['machine_abn_description'];
    $machine_abn_solution = $this_device_data['machine_abn_solution'];

    if (!empty($machine_abn_id)) {
        if (is_string($machine_abn_id)) {
            $machine_abn_id = json_decode($machine_abn_id, true);
        }
    }
    $machine_abn_text = array();
    $machine_abn_id_arr = array();
    if (!empty($machine_abn_id)) {
        if (!empty($machine_abn_description)) {
            if (is_string($machine_abn_description)) {
                $machine_abn_description = json_decode($machine_abn_description, true);
            }
        }
        if (!empty($machine_abn_solution)) {
            if (is_string($machine_abn_solution)) {
                $machine_abn_solution = json_decode($machine_abn_solution, true);
            }
        }
        foreach ($machine_abn_id as $key => $value) {
            $status_code = explode('_',$value);
            array_push($machine_abn_id_arr,$status_code[0]);
            array_push($machine_abn_text, array(
                'machine_abn_description' => $machine_abn_description[$key],
                'machine_abn_solution' => $machine_abn_solution[$key]
            ));
        }
    }

    $sensor_group = array();
    $machine_sensor_list = $this_device_data['machine_sensor_list'];
    $machine_main = $this_device_data['machine_main'];
    $machine_emeter = $this_device_data['machine_emeter'];
    $machine_servod = $this_device_data['machine_servod'];
    $machine_vibbearing = $this_device_data['machine_vibbearing'];
    $machine_vibMotor = $this_device_data['machine_vibMotor'];
    $machine_smb = $this_device_data['machine_smb'];
    if (!empty($machine_sensor_list)) {
        if (is_string($machine_sensor_list)) {
            $machine_sensor_list = json_decode($machine_sensor_list, true);
        }
    }
    if (!empty($machine_main)) {
        if (is_string($machine_main)) {
            $machine_main = json_decode($machine_main, true);
        }
    }
    if (!empty($machine_emeter)) {
        if (is_string($machine_emeter)) {
            $machine_emeter = json_decode($machine_emeter, true);
        }
    }
    if (!empty($machine_servod)) {
        if (is_string($machine_servod)) {
            $machine_servod = json_decode($machine_servod, true);
        }
    }
    if (!empty($machine_vibbearing)) {
        if (is_string($machine_vibbearing)) {
            $machine_vibbearing = json_decode($machine_vibbearing, true);
        }
    }
    if (!empty($machine_vibMotor)) {
        if (is_string($machine_vibMotor)) {
            $machine_vibMotor = json_decode($machine_vibMotor, true);
        }
    }
    if (!empty($machine_smb)) {
        if (is_string($machine_smb)) {
            $machine_smb = json_decode($machine_smb, true);
        }
    }

    $sensor_total_data = array(
        'main' => $machine_main,
        'emeter' => $machine_emeter,
        'servoD' => $machine_servod,
        'vibBearing' => $machine_vibbearing,
        'vibMotor' => $machine_vibMotor,
        'smb' => $machine_smb
    );
    $servoD_data_list = array(
        '0' => '無需處理',
        '1' => '伺服馬達回授異常',
        '3' => '電流過大',
        '4' => '散熱器溫度過高',
        '5' => '電壓異常(過高)',
        '6' => '電壓異常(過低)',
        '7' => '過負載',
        '9' => '驅動器程式錯誤'
    );
    $oilLevel_data_list = array(
        '0' => '油量充足(80~100%)',
        '1' => '油量正常(30~80%)',
        '2' => '油量不足警告(20~30%)',
        '3' => '油量不足(<20%)'
    );
    $adjust_rate = 0;//功因調整比例
    foreach ($machine_sensor_list as $key => $value) {
        $now_status = 'offline';
        if (!isset($sensor_group[$value['sensor_class_code']])) {
            $sensor_group[$value['sensor_class_code']] = array(
                'name' => $value['sensor_class_name'],
                'status' => 'offline',
                'data' => array()
            );
        }
        if ($value['sensor_table_name'] == 'emeter') {
            if ($value['sensor_code'] == 'TPF') {
                if (isset($sensor_total_data[$value['sensor_table_name']][$value['sensor_code']])) {
                    $sensor_total_data[$value['sensor_table_name']][$value['sensor_code']] = abs($sensor_total_data[$value['sensor_table_name']][$value['sensor_code']]);
                }
            }
        }
        if ($value['sensor_table_name'] == 'vibBearing' || $value['sensor_table_name'] == 'vibMotor') {
            $change_this_sensor_code = explode('_',$value['sensor_code']);
            array_shift($change_this_sensor_code);
            $value['sensor_code'] = implode('_', $change_this_sensor_code);
        }
        if (!isset($sensor_total_data[$value['sensor_table_name']][$value['sensor_code']])) {
            continue;
        }
        $now_status = 'normal';
        $this_sensor_value = $sensor_total_data[$value['sensor_table_name']][$value['sensor_code']];
        $this_sensor_stand = '-';
        if ($value['sensor_range'] == 'max') {
            $this_sensor_stand = '<' . ($value['sensor_error'] != null ? $value['sensor_error'] : ($value['sensor_warn'] != null ? $value['sensor_warn'] : ''));
            if ($value['sensor_warn'] != null) {
                if ($this_sensor_value >= (float)$value['sensor_warn']) {
                    $now_status = 'warning';
                }
            }
            if ($value['sensor_error'] != null) {
                if ($this_sensor_value >= (float)$value['sensor_error']) {
                    $now_status = 'error';
                }
            }
        } else if ($value['sensor_range'] == 'min') {
            $this_sensor_stand = '>' . ($value['sensor_error'] != null ? $value['sensor_error'] : ($value['sensor_warn'] != null ? $value['sensor_warn'] : ''));
            if ($value['sensor_warn'] != null) {
                if ($this_sensor_value <= (float)$value['sensor_warn']) {
                    $now_status = 'warning';
                }
            }
            if ($value['sensor_error'] != null) {
                if ($this_sensor_value <= (float)$value['sensor_error']) {
                    $now_status = 'error';
                }
            }
        } else if ($value['sensor_range'] == 'between') {
            if ($value['sensor_error'] != null) {
                $this_error_range = explode(',', $value['sensor_error']);
            } else if ($value['sensor_warn'] != null) {
                $this_warn_range = explode(',', $value['sensor_warn']);
            }
            
            if (isset($this_warn_range)) {
                $this_sensor_stand = $this_warn_range[0] . '~' . $this_warn_range[1];
                if ($this_sensor_value <= (float)$this_warn_range[0] || $this_sensor_value >= (float)$this_warn_range[1]) {
                    $now_status = 'warning';
                }
            }
            if (isset($this_error_range)) {
                $this_sensor_stand = $this_error_range[0] . '~' . $this_error_range[1];
                if ($this_sensor_value <= (float)$this_error_range[0] || $this_sensor_value >= (float)$this_error_range[1]) {
                    $now_status = 'error';
                }
            }
        }

        if (($sensor_group[$value['sensor_class_code']]['status'] == 'offline' && ($now_status == 'normal' || $now_status == 'warning' || $now_status == 'error')) || ($sensor_group[$value['sensor_class_code']]['status'] == 'normal' && ($now_status == 'warning' || $now_status == 'error')) || ($sensor_group[$value['sensor_class_code']]['status'] == 'warning' && $now_status == 'error')) {
            $sensor_group[$value['sensor_class_code']]['status'] = $now_status;
        }

        if ($value['sensor_table_name'] == 'emeter') {
            if ($value['sensor_code'] == 'TPF') {
                $adjust = abs($this_sensor_value);

                if ($adjust <= 0.95) {
                    $adjust_rate = round((0.8 - $adjust) / 0.01 * 0.1, 2);
                } else {
                    $adjust_rate = -1.5;
                }

                array_push($sensor_group[$value['sensor_class_code']]['data'], array(
                    'name' => '功因調整比例',
                    'stand' => '-',
                    'value' => $adjust_rate,
                    'status' => 'normal',
                    'unit' => '%'
                ));
            }
        }
        if ($value['sensor_table_name'] == 'servoD' && $value['sensor_code'] == 'err_code') {
            if (isset($servoD_data_list[$this_sensor_value])) {
                $this_sensor_value = $servoD_data_list[$this_sensor_value];
            }
        }
        if ($value['sensor_class_code'] == 'oilLevel') {
            if (isset($oilLevel_data_list[$this_sensor_value])) {
                $this_sensor_value = $oilLevel_data_list[$this_sensor_value];
            }
        }
        array_push($sensor_group[$value['sensor_class_code']]['data'], array(
            'name' => $value['sensor_name'],
            'stand' => $this_sensor_stand,
            'value' => $this_sensor_value,
            'status' => $now_status,
            'unit' => $value['sensor_unit']
        ));

        //畫圖表給最大最小值
        if ($value['sensor_table_name'] == 'emeter') {
            if ($value['sensor_code'] == 'current' || $value['sensor_code'] == 'voltage' || $value['sensor_code'] == 'volt_vubr') {
                $this_index = count($sensor_group[$value['sensor_class_code']]['data']) - 1;
                $sensor_group[$value['sensor_class_code']]['data'][$this_index]['min'] = $value['sensor_min'];
                $sensor_group[$value['sensor_class_code']]['data'][$this_index]['max'] = $value['sensor_max'];
            }
        }
    }

    $now_date = date("Y-m-d 08:00:00");//今天的日期
    $today_now_date = date("Y-m-d H:i:s");
    $now_date > $today_now_date ? $now_date = date("Y-m-d 08:00:00", strtotime("-1 day")) :  $now_date = $now_date;
    $power_expend = $this_device_data['power_expend'];
    if (!empty($power_expend)) {
        if (is_string($power_expend)) {
            $power_expend = json_decode($power_expend, true);
        }
        if (!isset($power_expend['time'])) {
            $power_expend['time'] = $now_date;
        }
        if (strtotime($today_now_date) - strtotime($power_expend['time']) > 3600) {
            $weekday = date("w", strtotime($now_date));
            $del_day = $weekday;
            //本週開始日期
            $this_week = date("Y-m-d 08:00:00", strtotime("$now_date -".$del_day." days"));
            $this_month = date("Y-m-d 08:00:00", mktime(0, 0, 0, date("m"), 1, date("Y")));
    
            $query_emeter = new apiJsonBody_query;
            // $query_emeter->setFields(['upload_at', 'RELEC']);
            $query_emeter->setTable($cus_id . '_' . $device_id . '_emeter');
            $query_emeter->addSymbols('upload_at', 'greater');
            $query_emeter->addWhere('upload_at', $now_date);
            $query_emeter->setLimit([0, 1]);
            $query_emeter->setOrderby(['asc','upload_at']);
            $query_emeter_data = $query_emeter->getApiJsonBody();
            $emeter_day = CommonSqlSyntax_Query_v2_5($query_emeter_data, "PostgreSQL", "no");
            if ($emeter_day['Response'] !== 'ok') {
                $emeter_day_data = [];
            } else {
                $emeter_day_data = $emeter_day['QueryTableData'];
            }
            $query_emeter = new apiJsonBody_query;
            // $query_emeter->setFields(['upload_at', 'RELEC']);
            $query_emeter->setTable($cus_id . '_' . $device_id . '_emeter');
            $query_emeter->addSymbols('upload_at', 'greater');
            $query_emeter->addWhere('upload_at', $this_week);
            $query_emeter->setLimit([0, 1]);
            $query_emeter->setOrderby(['asc','upload_at']);
            $query_emeter_data = $query_emeter->getApiJsonBody();
            $emeter_week = CommonSqlSyntax_Query_v2_5($query_emeter_data, "PostgreSQL", "no");
            if ($emeter_week['Response'] !== 'ok') {
                $emeter_week_data = [];
            } else {
                $emeter_week_data = $emeter_week['QueryTableData'];
            }
            $query_emeter = new apiJsonBody_query;
            // $query_emeter->setFields(['upload_at', 'RELEC']);
            $query_emeter->setTable($cus_id . '_' . $device_id . '_emeter');
            $query_emeter->addSymbols('upload_at', 'greater');
            $query_emeter->addWhere('upload_at', $this_month);
            $query_emeter->setLimit([0, 1]);
            $query_emeter->setOrderby(['asc','upload_at']);
            $query_emeter_data = $query_emeter->getApiJsonBody();
            $emeter_month = CommonSqlSyntax_Query_v2_5($query_emeter_data, "PostgreSQL", "no");
            if ($emeter_month['Response'] !== 'ok') {
                $emeter_month_data = [];
            } else {
                $emeter_month_data = $emeter_month['QueryTableData'];
            }
    
            $power_expend = array();
            if (!empty($emeter_day_data)) {
                $day_RELEC = $emeter_day_data[0]['RELEC'];
                $power_expend['day'] = $day_RELEC;
            } else {
                $power_expend['day'] = 0;
            }
            if (!empty($emeter_week_data)) {
                $week_RELEC = $emeter_week_data[0]['RELEC'];
                $power_expend['week'] = $week_RELEC;
            } else {
                $power_expend['week'] = 0;
            }
            if (!empty($emeter_month_data)) {
                $month_RELEC = $emeter_month_data[0]['RELEC'];
                $power_expend['month'] = $month_RELEC;
            } else {
                $power_expend['month'] = 0;
            }
            $power_expend['time'] = $today_now_date;
            $update_data['mes_device_status_' . $cus_id . '_' . $device_id] = array(
                'power_expend' => $power_expend
            );
            CommonUpdate($update_data, 'Redis', null);
        }
    } else {
        $weekday = date("w", strtotime($now_date));
        $del_day = $weekday;
        //本週開始日期
        $this_week = date("Y-m-d 08:00:00", strtotime("$now_date -".$del_day." days"));
        $this_month = date("Y-m-d 08:00:00", mktime(0, 0, 0, date("m"), 1, date("Y")));
        // $query_emeter = new apiJsonBody_query;
        // // $query_emeter->setFields(['upload_at', 'RELEC']);
        // $query_emeter->setTable($cus_id . '_' . $device_id . '_emeter');
        // $query_emeter->addSymbols('combine', array('upload_at' => array('equal')));
        // $query_emeter->addWhere('combine', array('upload_at' => array('subcondition_1')));
        // $query_emeter->addSymbols('combine', array('upload_at' => array('equal')));
        // $query_emeter->addWhere('combine', array('upload_at' => array('subcondition_2')));
        // $query_emeter->addSymbols('combine', array('upload_at' => array('equal')));
        // $query_emeter->addWhere('combine', array('upload_at' => array('subcondition_3')));
        // // $query_emeter->addSymbols('upload_at', 'greater');
        // // $query_emeter->addWhere('upload_at', $now_date);
        // // $query_emeter->setLimit([0, 3]);
        // $query_emeter->setOrderby(['asc','upload_at']);
        // $query_emeter->addSubquery('subcondition_1');
        // $query_emeter_subcondition = $query_emeter->getSubquery('subcondition_1');
        // $query_emeter_subcondition->setFields(['upload_at']);
        // $query_emeter_subcondition->setTable($cus_id . '_' . $device_id . '_emeter');
        // $query_emeter_subcondition->addSymbols('upload_at', 'greater');
        // $query_emeter_subcondition->addWhere('upload_at', $now_date);
        // $query_emeter_subcondition->setLimit([0,1]);
        // $query_emeter_subcondition->setOrderby(['asc','upload_at']);
        // $query_emeter->addSubquery('subcondition_2');
        // $query_emeter_subcondition = $query_emeter->getSubquery('subcondition_2');
        // $query_emeter_subcondition->setFields(['upload_at']);
        // $query_emeter_subcondition->setTable($cus_id . '_' . $device_id . '_emeter');
        // $query_emeter_subcondition->addSymbols('upload_at', 'greater');
        // $query_emeter_subcondition->addWhere('upload_at', $last_week);
        // $query_emeter_subcondition->setLimit([0,1]);
        // $query_emeter_subcondition->setOrderby(['asc','upload_at']);
        // $query_emeter->addSubquery('subcondition_3');
        // $query_emeter_subcondition = $query_emeter->getSubquery('subcondition_3');
        // $query_emeter_subcondition->setFields(['upload_at']);
        // $query_emeter_subcondition->setTable($cus_id . '_' . $device_id . '_emeter');
        // $query_emeter_subcondition->addSymbols('upload_at', 'greater');
        // $query_emeter_subcondition->addWhere('upload_at', $this_month);
        // $query_emeter_subcondition->setLimit([0,1]);
        // $query_emeter_subcondition->setOrderby(['asc','upload_at']);
        // // $query_emeter_data = $query_emeter->getApiJsonBody();
        // // $emeter = CommonSqlSyntax_Query_v2_5($query_emeter_data, "PostgreSQL", "no");
        // // if ($emeter['Response'] !== 'ok') {
        // //     $emeter_data = [];
        // // } else {
        // //     $emeter_data = $emeter['QueryTableData'];
        // // }

        $query_emeter = new apiJsonBody_query;
        // $query_emeter->setFields(['upload_at', 'RELEC']);
        $query_emeter->setTable($cus_id . '_' . $device_id . '_emeter');
        $query_emeter->addSymbols('upload_at', 'greater');
        $query_emeter->addWhere('upload_at', $now_date);
        $query_emeter->setLimit([0, 1]);
        $query_emeter->setOrderby(['asc','upload_at']);
        $query_emeter_data = $query_emeter->getApiJsonBody();
        $emeter_day = CommonSqlSyntax_Query_v2_5($query_emeter_data, "PostgreSQL", "no");
        if ($emeter_day['Response'] !== 'ok') {
            $emeter_day_data = [];
        } else {
            $emeter_day_data = $emeter_day['QueryTableData'];
        }
        $query_emeter = new apiJsonBody_query;
        // $query_emeter->setFields(['upload_at', 'RELEC']);
        $query_emeter->setTable($cus_id . '_' . $device_id . '_emeter');
        $query_emeter->addSymbols('upload_at', 'greater');
        $query_emeter->addWhere('upload_at', $this_week);
        $query_emeter->setLimit([0, 1]);
        $query_emeter->setOrderby(['asc','upload_at']);
        $query_emeter_data = $query_emeter->getApiJsonBody();
        $emeter_week = CommonSqlSyntax_Query_v2_5($query_emeter_data, "PostgreSQL", "no");
        if ($emeter_week['Response'] !== 'ok') {
            $emeter_week_data = [];
        } else {
            $emeter_week_data = $emeter_week['QueryTableData'];
        }
        $query_emeter = new apiJsonBody_query;
        // $query_emeter->setFields(['upload_at', 'RELEC']);
        $query_emeter->setTable($cus_id . '_' . $device_id . '_emeter');
        $query_emeter->addSymbols('upload_at', 'greater');
        $query_emeter->addWhere('upload_at', $this_month);
        $query_emeter->setLimit([0, 1]);
        $query_emeter->setOrderby(['asc','upload_at']);
        $query_emeter_data = $query_emeter->getApiJsonBody();
        $emeter_month = CommonSqlSyntax_Query_v2_5($query_emeter_data, "PostgreSQL", "no");
        if ($emeter_month['Response'] !== 'ok') {
            $emeter_month_data = [];
        } else {
            $emeter_month_data = $emeter_month['QueryTableData'];
        }

        $power_expend = array();
        if (!empty($emeter_day_data)) {
            $day_RELEC = $emeter_day_data[0]['RELEC'];
            $power_expend['day'] = $day_RELEC;
        } else {
            $power_expend['day'] = 0;
        }
        if (!empty($emeter_week_data)) {
            $week_RELEC = $emeter_week_data[0]['RELEC'];
            $power_expend['week'] = $week_RELEC;
        } else {
            $power_expend['week'] = 0;
        }
        if (!empty($emeter_month_data)) {
            $month_RELEC = $emeter_month_data[0]['RELEC'];
            $power_expend['month'] = $month_RELEC;
        } else {
            $power_expend['month'] = 0;
        }
        $power_expend['time'] = $today_now_date;
        $update_data['mes_device_status_' . $cus_id . '_' . $device_id] = array(
            'power_expend' => $power_expend
        );
        CommonUpdate($update_data, 'Redis', null);
    }

    $electricity_RELEC = array(
        array('interval' => '本日', 'powerUsed' => '-', 'estimatedCost' => 0),
        array('interval' => '本周', 'powerUsed' => '-', 'estimatedCost' => 0),
        array('interval' => '本月', 'powerUsed' => '-', 'estimatedCost' => 0)
    );
    if (isset($machine_emeter['RELEC'])) {
        $electricityBill = 0;
        $this_month = (int)date('m', strtotime($now_date));
        $this_total_day = (int)date("t", strtotime($now_date));
    
        $this_day_RELEC = round($machine_emeter['RELEC'] - $power_expend['day'], 2);
        $this_week_RELEC = round($machine_emeter['RELEC'] - $power_expend['week'], 2);
        $this_month_RELEC = round($machine_emeter['RELEC'] - $power_expend['month'], 2);
        $adjust_rate = round($adjust_rate/100, 4);
        
        if ($this_month>=6 && $this_month<=9) {
            $electricityBill = 60 * 236.20;
            $day_electricityBill = round($electricityBill / $this_total_day + $this_day_RELEC * 2.58 * (1 + $adjust_rate), 1);
            $week_electricityBill = round($electricityBill / 7 + $this_week_RELEC * 2.58 * (1 + $adjust_rate), 1);
            $month_electricityBill = round($electricityBill + $this_month_RELEC * 2.58 * (1 + $adjust_rate), 1);
        } else {
            $electricityBill = 60 * 173.20;
            $day_electricityBill = round($electricityBill / $this_total_day + $this_day_RELEC * 2.45 * (1 + $adjust_rate), 1);
            $week_electricityBill = round($electricityBill / 7 + $this_week_RELEC * 2.45 * (1 + $adjust_rate), 1);
            $month_electricityBill = round($electricityBill + $this_month_RELEC * 2.45 * (1 + $adjust_rate), 1);
        }
    
        $electricity_RELEC = array(
            array('interval' => '本日', 'powerUsed' => $this_day_RELEC, 'estimatedCost' => $day_electricityBill),
            array('interval' => '本周', 'powerUsed' => $this_week_RELEC, 'estimatedCost' => $week_electricityBill),
            array('interval' => '本月', 'powerUsed' => $this_month_RELEC, 'estimatedCost' => $month_electricityBill)
        );
    }

    array_push($device_back_data, array(
        'device_id' => $device_id,
        'device_name' => $device_name,
        'device_model' => $device_model,
        'category' => $category,
        'machine_image' => $machine_image,
        'machine_status' => $machine_status,
        'device_run_time' => $device_run_time,
        'device_activation' => $device_activation,
        'rpm' => $rpm,
        'device_day_count' => $device_day_count,
        'device_now_count' => $device_now_count,
        'wire_weight' => $wire_weight,
        'device_stackBar' => $stack_bar_information,
        'machine_camera' => $machine_camera,
        'operatelog_information' => $operatelog_information,
        'alarmHistory_information' => $alarmHistory_information,
        'machine_light_value' => $machine_light_value,
        'diagnosis_message' => $diagnosis_message,
        'machine_abn_text' => $machine_abn_text,
        'machine_abn_id' => $machine_abn_id_arr,
        'sensor_group' => $sensor_group,
        'electricity_RELEC' => $electricity_RELEC
    ));

    $returnData['QueryTableData'] = $device_back_data;
    $returnData['Response'] = 'ok';
    $returnData['page'] = 'elecboard';
    return $returnData;
}

function sort_device($a, $b){
    return ($a['device_id'] > $b['device_id']) ? 1 : -1;
}

function QueryMachineCamera($params)//查詢機台ipcam
{
    $device_id = $params->deviceID;

    $query_machine_camera = new apiJsonBody_query;
    $query_machine_camera->setFields(['device_id', 'camera_name', 'url']);
    $query_machine_camera->setTable('machine_camera');
    $query_machine_camera->addSymbols('device_id', 'equal');
    $query_machine_camera->addWhere('device_id', $device_id);
    $query_machine_camera_data = $query_machine_camera->getApiJsonBody();
    $machine_camera = CommonSqlSyntax_Query($query_machine_camera_data, "MySQL", "no");
    
    return $machine_camera;
}

function UpdateMachineCamera($params)//查詢機台ipcam
{
    $cus_id = $params->cusID;
    $device_id = $params->deviceID;
    $ipData = $params->ipData;
    $modifier = $params->modifier;

    $update_machine_camera_data = array(
        'old_device_id' => array(),
        'old_camera_name' => array(),
        'url' => array(),
        'modifier' => array()
    );
    $machine_camera_data = array();
    foreach ($ipData as $key => $value) {
        $url = 'http://' . $value->ip . ':' . $value->port . '/GetData.cgi?CH=1&WebUser=admin&WebPass=haobangbang';
        array_push($update_machine_camera_data['old_device_id'], $device_id);
        array_push($update_machine_camera_data['old_camera_name'], $value->camera_name);
        array_push($update_machine_camera_data['url'], $url);
        array_push($update_machine_camera_data['modifier'], $modifier);
        array_push($machine_camera_data, array(
            'url' => $url,
            'camera_name' => $value->camera_name
        ));
    }

    $machine_camera = CommonUpdate($update_machine_camera_data, "MySQL", "machine_camera");

    $update_data = array(
        'mes_device_status_' . $cus_id . '_' . $device_id => array(
            'machine_camera' => $machine_camera_data
        )  
    );
    CommonUpdate($update_data, 'Redis', null);
    return $machine_camera;
}

function get_heading_machine_data($params)
{
    //回傳的資料
    $returnData['QueryTableData'] = [];

    //現在的時間
    $now_time = strtotime(date("Y-m-d H:i:s"));

    // 查詢machine_status，機台當前狀態
    // 機台名稱、目前工單編號、是否有首件檢查1=有，機台運作狀態、機台狀態Q=非故障
    $fields = ['device_name', 'work_code', 'status', 'first_inspection', 'machine_detail', 'mac_status'];
    $data = array(
        'condition_1' => array(
            'fields' => $fields,
            'limit' => ["ALL"],
            'table' => 'machine_status_head'
        )
    );
    $machine_status_head = CommonSqlSyntax_Query($data, "MySQL");
    if ($machine_status_head['Response'] !== 'ok') {
        return $machine_status_head;
    } else if (count($machine_status_head['QueryTableData']) == 0) {
        $machine_status_head['Response'] = "no data";
        return $machine_status_head;
    }
    $machine_status_data = $machine_status_head['QueryTableData'];

    //取得所有機台編號
    $device_array = get_device_array($machine_status_data);

    //查詢machine_abn，機台異常資料
    $machine_abn = CommonTableQuery('MySQL', 'machine_abn');
    if ($machine_abn['Response'] !== 'ok') {
        return $machine_abn;
    } else if (count($machine_abn['QueryTableData']) == 0) {
        $machine_abn['Response'] = "no data";
        return $machine_abn;
    }
    $machine_abn_data = $machine_abn['QueryTableData'];
    $machine_abn_code = [];
    for ($i = 0; $i < count($machine_abn_data); $i++) {
        $machine_abn_code[$machine_abn_data[$i]['name']] = array(
            'err_code' => $machine_abn_data[$i]['err_code'],
            'value' => $machine_abn_data[$i]['value']
        );
    }

    //查詢機台今日工單
    $intervaltime = new stdClass();
    $intervaltime->sch_prod_date = array([date("Y-m-d 00:00:00"), date("Y-m-d 23:59:59")]);
    $whereAttr = new stdClass();
    $whereAttr->device_name = $device_array;
    $symbols = new stdClass();
    $symbols->device_name = array_map('symbols_equal', $device_array);
    $data = array(
        'condition_1' => array(
            'table' => 'work_order',
            'intervaltime' => $intervaltime,
            'where' => $whereAttr,
            'limit' => ['ALL'],
            'symbols' => $symbols
        )
    );
    $work_order = CommonSqlSyntax_Query($data, 'MsSQL');
    if ($work_order['Response'] !== 'ok') {
    } else if (count($work_order['QueryTableData']) == 0) {
        $work_order['Response'] = "no data";
    }
    $work_order_data = $work_order['QueryTableData'];

    $device_work_order = array();
    //將今日打頭的工單存取
    foreach ($work_order_data as $key => $value) {
        if (!isset($device_work_order[$value['device_name']])) {
            $device_work_order[$value['device_name']] = [];
        }
        array_push($device_work_order[$value['device_name']], $value);
    }

    // 查詢機台機型
    $whereAttr = new stdClass();
    $whereAttr->name = $device_array;
    $symbols = new stdClass();
    $symbols->name = array_map('symbols_equal', $device_array);
    $data = array(
        'condition_1' => array(
            'table' => 'device_box',
            'where' => $whereAttr,
            'limit' => ['ALL'],
            'symbols' => $symbols
        )
    );
    $device_box = CommonSqlSyntax_Query($data, "MsSQL");
    if ($device_box['Response'] !== 'ok' || count($device_box['QueryTableData']) == 0) {
        $device_box_data = [];
    } else {
        $device_box_data = $device_box['QueryTableData'];
    }

    $device_device_box = array();
    $device_model = array();
    foreach ($device_box_data as $key => $value) {
        if (!isset($device_device_box[$value['name']])) {
            $device_device_box[$value['name']] = array();
        }
        $device_device_box[$value['name']] = $value;
        array_push($device_model, $value['model']);
    }

    if (!empty($device_model)) {
        //查詢machine_status_list，機台燈號
        $whereAttr = new stdClass();
        $whereAttr->model = $device_model;
        $symbols = new stdClass();
        $symbols->model = array_map('symbols_equal', $device_model);
        $data = array(
            'condition_1' => array(
                'table' => 'machine_status_list',
                'where' => $whereAttr,
                'limit' => ['ALL'],
                'symbols' => $symbols
            )
        );
        $machine_status_list = CommonSqlSyntax_Query($data, "MySQL");
        if ($machine_status_list['Response'] !== 'ok' || count($machine_status_list['QueryTableData']) == 0) {
            $machine_status_list_data = [];
        } else {
            $machine_status_list_data = $machine_status_list['QueryTableData'];
        }
        foreach ($device_device_box as $device_device_box_key => $device_device_box_value) {
            foreach ($machine_status_list_data as $machine_status_list_data_key => $machine_status_list_data_value) {
                if ($device_device_box_value['model'] == $machine_status_list_data_value['model']) {
                    if (is_string($machine_status_list_data_value['light_list'])) {
                        $machine_status_list_data_value['light_list'] = json_decode($machine_status_list_data_value['light_list'], true);
                    }
                    $device_device_box[$device_device_box_key]['light_list'] =  $machine_status_list_data_value['light_list'];
                }
            }
        }
    }

    //用該值來儲存資料
    $machine_device_data = $machine_status_data;

    foreach ($machine_device_data as $key => $value) {
        if (is_string($value['machine_detail'])) {
            $value['machine_detail'] = json_decode($value['machine_detail'], true);
        }
        //機台狀態
        if ($value['mac_status'] == 'Q') {
            if (gettype($value['machine_detail']) == 'array') {
                if ($now_time - 600 > strtotime($value['machine_detail']['timestamp'])) {
                    $machine_device_data[$key]['now_status'] = 'S';
                } else {
                    $machine_detail = $value['machine_detail'];
                    if ($machine_detail['OPR'] == 1) {
                        $machine_device_data[$key]['now_status'] = 'R'; //運轉
                    } else {
                        $machine_device_data[$key]['now_status'] = 'Q'; //閒置
                    }
                    if (isset($device_device_box[$value['device_name']])) {
                        if (isset($device_device_box[$value['device_name']]['light_list'])) {
                            foreach ($machine_abn_code as $machine_abn_code_key => $machine_abn_code_value) {
                                if (isset($device_device_box[$value['device_name']]['light_list'][$machine_abn_code_key])) {
                                    if ($machine_abn_code_value['value'] == $machine_detail[$machine_abn_code_key]) {
                                        if ($machine_abn_code_key == 'in_lube') {
                                            if ($machine_detail['OPR'] == 1) {
                                                $machine_device_data[$key]['now_status'] = 'H';
                                                break;
                                            }
                                        } else {
                                            $machine_device_data[$key]['now_status'] = 'H';
                                            break;
                                        }
                                    }
                                }
                            }
                        } else {
                            //沒有機型資料
                            $machine_device_data[$key]['now_status'] = 'H';
                        }
                    } else {
                        //沒有機台資料
                        $machine_device_data[$key]['now_status'] = 'H';
                    }
                }
            }
        } else if ($value['mac_status'] == 'H') {
            $machine_device_data[$key]['now_status'] = 'H';
        }

        //機台轉速
        if (isset($device_device_box[$value['device_name']])) {
            $machine_device_data[$key]['speed'] = round($device_device_box[$value['device_name']]['capacity_hr'] / 60, 0);
        }

        //目前支數
        if ($value['machine_detail'] != "") {
            if (isset($value['machine_detail']['cnt'])) {
                $machine_device_data[$key]['count'] = $value['machine_detail']['cnt'];
            }
        }

        $machine_device_data[$key]['day_work_order_count'] = 0;
        $machine_device_data[$key]['remain_work_order_count'] = 0;

        //今日工單總量、餘量
        if (!empty($device_work_order)) {
            if (isset($device_work_order[$value['device_name']])) {
                //今日工單總數量
                $machine_device_data[$key]['day_work_order_count'] = count($device_work_order[$value['device_name']]);
                $remain_work_order_count = 0;
                foreach ($device_work_order[$value['device_name']] as $device_work_order_key => $device_work_order_value) {
                    //若該工單尚未完成則加入工單餘量
                    if ($device_work_order_value['status'] == 0 || $device_work_order_value['status'] == 'S') {
                        $remain_work_order_count++;
                    }
                }
                $machine_device_data[$key]['remain_work_order_count'] = $remain_work_order_count;

                if (empty(array_search($value['work_code'], array_column($device_work_order[$value['device_name']], 'code')))) {
                    $machine_device_data[$key]['day_work_order_count']++;
                } else {
                    $work_order_data_position = array_search($value['work_code'], array_column($device_work_order[$value['device_name']], 'code'));
                    $machine_device_data[$key]['work_code_qty'] = $device_work_order[$value['device_name']][$work_order_data_position]['work_qty'];
                    $machine_device_data[$key]['remain_work_order_count']--;
                }
            } else {
                if ($value['work_code'] != "") {
                    $machine_device_data[$key]['day_work_order_count']++;
                }
            }
        } else {
            if ($value['work_code'] != "") {
                $machine_device_data[$key]['day_work_order_count']++;
            }
        }

        //正在做的工單進度
        if (!isset($machine_device_data[$key]['work_code_qty'])) {
            //查詢目前工單
            $whereAttr = new stdClass();
            $whereAttr->code = [$value['work_code']];
            $symbols = new stdClass();
            $symbols->code = ["equal"];
            $data = array(
                'condition_1' => array(
                    'table' => 'work_order',
                    'where' => $whereAttr,
                    'limit' => [0, 1],
                    'symbols' => $symbols
                )
            );
            $this_work_order = CommonSqlSyntax_Query($data, 'MsSQL');
            if ($this_work_order['Response'] !== 'ok') {
                return $this_work_order;
            } else if (count($this_work_order['QueryTableData']) == 0) {
                $machine_device_data[$key]['work_code_qty'] = '--';
            } else {
                $this_work_order_data = $this_work_order['QueryTableData'];
                $machine_device_data[$key]['work_code_qty'] = $this_work_order_data[0]['work_qty'];
            }
        }

        //工單完成率
        if (isset($machine_device_data[$key]['count']) && isset($machine_device_data[$key]['work_code_qty']) && is_numeric($machine_device_data[$key]['work_code_qty'])) {
            $machine_device_data[$key]['work_code_complete'] = round(round($machine_device_data[$key]['count'] / $machine_device_data[$key]['work_code_qty'], 2) * 100, 2);
        }

        array_push($returnData['QueryTableData'], array(
            'product_line' => $params->group_name, //產線
            'device_name' => isset($machine_device_data[$key]['device_name']) ? $machine_device_data[$key]['device_name'] : '--', //機台名稱
            'now_status' => isset($machine_device_data[$key]['now_status']) ? $machine_device_data[$key]['now_status'] : '--', //狀態
            'speed' => isset($machine_device_data[$key]['speed']) ? $machine_device_data[$key]['speed'] : '--', //速度
            // 'count' => isset($machine_device_data[$key]['count']) ? $machine_device_data[$key]['count'] : '--',//目前支數
            'work_code_qty' => isset($machine_device_data[$key]['work_code_qty']) ? $machine_device_data[$key]['work_code_qty'] : '--', //目前工單需求支數
            // 'work_code_complete' => isset($machine_device_data[$key]['work_code_complete']) ? $machine_device_data[$key]['work_code_complete'] : '--',//當前工單完成率
            'workCode' => isset($machine_device_data[$key]['work_code']) ? $machine_device_data[$key]['work_code'] : '--', //當前工單
            'day_work_order_count' => isset($machine_device_data[$key]['day_work_order_count']) ? $machine_device_data[$key]['day_work_order_count'] : '--', //工單總量
            'work_order_count' => isset($machine_device_data[$key]['remain_work_order_count']) ? $machine_device_data[$key]['remain_work_order_count'] : '--', //工單餘量
        ));
    }

    $returnData['Response'] = 'ok';
    $returnData['page'] = 'elecboard';
    return $returnData;
}

function get_thd_machine_data($params)
{
    //回傳的資料
    $returnData['QueryTableData'] = [];

    //現在的時間
    $now_time = strtotime(date("Y-m-d H:i:s"));

    // 查詢machine_status，機台當前狀態
    // 機台名稱、目前工單編號、是否有首件檢查1=有，機台運作狀態、機台狀態Q=非故障
    $fields = ['device_name', 'work_code', 'status', 'first_inspection', 'machine_detail', 'mac_status'];
    $data = array(
        'condition_1' => array(
            'fields' => $fields,
            'limit' => ["ALL"],
            'table' => 'machine_status_thd'
        )
    );
    $machine_status_thd = CommonSqlSyntax_Query($data, "MySQL");
    if ($machine_status_thd['Response'] !== 'ok') {
        return $machine_status_thd;
    } else if (count($machine_status_thd['QueryTableData']) == 0) {
        $machine_status_thd['Response'] = "no data";
        return $machine_status_thd;
    }
    $machine_status_data = $machine_status_thd['QueryTableData'];

    //取得所有機台編號
    $device_array = get_device_array($machine_status_data);

    //開始時間
    if ($now_time >= strtotime(date("Y-m-d 08:00:00"))) {
        $startTime = date("Y-m-d 08:00:00");
    } else {
        $startTime = date("Y-m-d 08:00:00", strtotime(date("Y-m-d 08:00:00") - 86400));
    }

    //查詢工單上線數量
    $whereAttr = new stdClass();
    $whereAttr->device_name = $device_array;
    $symbols = new stdClass();
    $symbols->device_name = array_map('symbols_equal', $device_array);
    $intervaltime = array(
        'upload_at' => array(array($startTime, date("Y-m-d H:i:s", $now_time)))
    );
    $data = array(
        'condition_1' => array(
            'intervaltime' => $intervaltime,
            'fields' => ['upload_at', 'work_code', 'project_id', 'device_name', 'status'],
            'table' => 'work_code_use',
            'orderby' => ['asc', 'upload_at'],
            'limit' => ['ALL'],
            'symbols' => $symbols,
            'where' => $whereAttr,
        )
    );
    $work_code_use = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    if ($work_code_use['Response'] !== 'ok') {
        return $work_code_use;
    }
    $work_code_use_data = $work_code_use['QueryTableData'];

    $work_code_array = get_work_code_array($work_code_use_data);

    //查詢machine_abn，機台異常資料
    $machine_abn = CommonTableQuery('MySQL', 'machine_abn');
    if ($machine_abn['Response'] !== 'ok') {
        return $machine_abn;
    } else if (count($machine_abn['QueryTableData']) == 0) {
        $machine_abn['Response'] = "no data";
        return $machine_abn;
    }
    $machine_abn_data = $machine_abn['QueryTableData'];
    $machine_abn_code = [];
    for ($i = 0; $i < count($machine_abn_data); $i++) {
        $machine_abn_code[$machine_abn_data[$i]['name']] = array(
            'err_code' => $machine_abn_data[$i]['err_code'],
            'value' => $machine_abn_data[$i]['value']
        );
    }

    if (!empty($work_code_array)) {
        //查詢機台今日工單
        $whereAttr = new stdClass();
        $whereAttr->code = $work_code_array;
        $symbols = new stdClass();
        $symbols->code = array_map('symbols_equal', $work_code_array);
        $data = array(
            'condition_1' => array(
                'table' => 'work_order',
                'where' => $whereAttr,
                'limit' => ['ALL'],
                'symbols' => $symbols
            )
        );
        $work_order = CommonSqlSyntax_Query($data, 'MsSQL');
        if ($work_order['Response'] !== 'ok') {
        } else if (count($work_order['QueryTableData']) == 0) {
            $work_order['Response'] = "no data";
        }
        $work_order_data = $work_order['QueryTableData'];
    }

    $device_work_order = array();
    $device_work_time = array(); //機台工單上線時間
    //將今日輾牙的工單存取
    foreach ($work_code_use_data as $key => $value) {
        if (!isset($device_work_order[$value['device_name']])) {
            $device_work_order[$value['device_name']] = [];
        }
        //如果已經有同一張工單的紀錄，則記錄他最新的狀態
        if (empty(array_search($value['work_code'], array_column($device_work_order[$value['device_name']], 'code')))) {
            array_push($device_work_order[$value['device_name']], $value);
        } else {
            $work_order_data_position = array_search($value['work_code'], array_column($device_work_order[$value['device_name']], 'code'));
            $device_work_order[$value['device_name']][$work_order_data_position]['status'] = $value['status'];
        }
        if (!isset($device_work_time[$value['device_name']])) {
            $device_work_time[$value['device_name']] = [];
        }
        if ($value['status'] == 'S') {
            if (empty($device_work_time[$value['device_name']])) {
                $device_work_time[$value['device_name']] = $value['upload_at'];
            } else {
                if (strtotime($device_work_time[$value['device_name']]) <= strtotime($value['upload_at'])) {
                    $device_work_time[$value['device_name']] = $value['upload_at'];
                }
            }
        } else if ($value['status'] == 'E') {
            if (!empty($device_work_time[$value['device_name']])) {
                if (strtotime($device_work_time[$value['device_name']]) <= strtotime($value['upload_at'])) {
                    $device_work_time[$value['device_name']] = '';
                }
            }
        }
    }

    // 查詢機台機型
    $whereAttr = new stdClass();
    $whereAttr->name = $device_array;
    $symbols = new stdClass();
    $symbols->name = array_map('symbols_equal', $device_array);
    $data = array(
        'condition_1' => array(
            'table' => 'device_box',
            'where' => $whereAttr,
            'limit' => ['ALL'],
            'symbols' => $symbols
        )
    );
    $device_box = CommonSqlSyntax_Query($data, "MsSQL");
    if ($device_box['Response'] !== 'ok' || count($device_box['QueryTableData']) == 0) {
        $device_box_data = [];
    } else {
        $device_box_data = $device_box['QueryTableData'];
    }

    $device_device_box = array();
    $device_model = array();
    foreach ($device_box_data as $key => $value) {
        if (!isset($device_device_box[$value['name']])) {
            $device_device_box[$value['name']] = array();
        }
        $device_device_box[$value['name']] = $value;
        array_push($device_model, $value['model']);
    }

    if (!empty($device_model)) {
        //查詢machine_status_list，機台燈號
        $whereAttr = new stdClass();
        $whereAttr->model = $device_model;
        $symbols = new stdClass();
        $symbols->model = array_map('symbols_equal', $device_model);
        $data = array(
            'condition_1' => array(
                'table' => 'machine_status_list',
                'where' => $whereAttr,
                'limit' => ['ALL'],
                'symbols' => $symbols
            )
        );
        $machine_status_list = CommonSqlSyntax_Query($data, "MySQL");
        if ($machine_status_list['Response'] !== 'ok' || count($machine_status_list['QueryTableData']) == 0) {
            $machine_status_list_data = [];
        } else {
            $machine_status_list_data = $machine_status_list['QueryTableData'];
        }
        foreach ($device_device_box as $device_device_box_key => $device_device_box_value) {
            foreach ($machine_status_list_data as $machine_status_list_data_key => $machine_status_list_data_value) {
                if ($device_device_box_value['model'] == $machine_status_list_data_value['model']) {
                    if (is_string($machine_status_list_data_value['light_list'])) {
                        $machine_status_list_data_value['light_list'] = json_decode($machine_status_list_data_value['light_list'], true);
                    }
                    $device_device_box[$device_device_box_key]['light_list'] =  $machine_status_list_data_value['light_list'];
                }
            }
        }
    }

    //用該值來儲存資料
    $machine_device_data = $machine_status_data;

    foreach ($machine_device_data as $key => $value) {
        if (is_string($value['machine_detail'])) {
            $value['machine_detail'] = json_decode($value['machine_detail'], true);
        }
        //機台狀態
        if ($value['mac_status'] == 'Q') {
            if (gettype($value['machine_detail']) == 'array') {
                if ($now_time - 600 > strtotime($value['machine_detail']['timestamp'])) {
                    $machine_device_data[$key]['now_status'] = 'S';
                } else {
                    $machine_detail = $value['machine_detail'];
                    if ($machine_detail['OPR'] == 1) {
                        $machine_device_data[$key]['now_status'] = 'R'; //運轉
                    } else {
                        $machine_device_data[$key]['now_status'] = 'Q'; //閒置
                    }
                    if (isset($device_device_box[$value['device_name']])) {
                        if (isset($device_device_box[$value['device_name']]['light_list'])) {
                            foreach ($machine_abn_code as $machine_abn_code_key => $machine_abn_code_value) {
                                if (isset($device_device_box[$value['device_name']]['light_list'][$machine_abn_code_key])) {
                                    if ($machine_abn_code_key != 'in_lube') {
                                        if ($machine_abn_code_value['value'] == $machine_detail[$machine_abn_code_key]) {
                                            $machine_device_data[$key]['now_status'] = 'H';
                                            break;
                                        }
                                    }
                                }
                            }
                        } else {
                            //沒有機型資料
                            $machine_device_data[$key]['now_status'] = 'H';
                        }
                    } else {
                        //沒有機台資料
                        $machine_device_data[$key]['now_status'] = 'H';
                    }
                }
            }
        } else if ($value['mac_status'] == 'H') {
            $machine_device_data[$key]['now_status'] = 'H';
        }

        //機台轉速
        if (isset($device_device_box[$value['device_name']])) {
            $machine_device_data[$key]['speed'] = round($device_device_box[$value['device_name']]['capacity_hr'] / 60, 0);
        }

        //目前支數
        if ($value['machine_detail'] != "") {
            if (isset($value['machine_detail']['cnt'])) {
                $machine_device_data[$key]['count'] = $value['machine_detail']['cnt'];
            }
        }

        if (empty($device_work_time[$value['device_name']])) {
            $device_work_time[$value['device_name']] = '';
        }
        $device_now_count = get_start_count($value['device_name'], $device_work_time[$value['device_name']], $machine_device_data[$key]['count']);
        $machine_device_data[$key]['count'] = $device_now_count;
        // return $device_now_count;
        $machine_device_data[$key]['machine_detail'] = $value['machine_detail'];

        //正在做的工單進度
        if ($value['work_code'] != "") {
            //查詢目前工單
            $whereAttr = new stdClass();
            $whereAttr->code = [$value['work_code']];
            $symbols = new stdClass();
            $symbols->code = ["equal"];
            $data = array(
                'condition_1' => array(
                    'table' => 'work_order',
                    'where' => $whereAttr,
                    'limit' => [0, 1],
                    'symbols' => $symbols
                )
            );
            $this_work_order = CommonSqlSyntax_Query($data, 'MsSQL');
            if ($this_work_order['Response'] !== 'ok') {
                return $this_work_order;
            } else if (count($this_work_order['QueryTableData']) == 0) {
                // $machine_device_data[$key]['work_code_qty'] = '--';
            } else {
                $this_work_order_data = $this_work_order['QueryTableData'];
                $machine_device_data[$key]['work_code_qty'] = $this_work_order_data[0]['work_qty'];
            }
        }

        //工單完成率
        if (isset($machine_device_data[$key]['count']) && isset($machine_device_data[$key]['work_code_qty']) && is_numeric($machine_device_data[$key]['work_code_qty'])) {
            $machine_device_data[$key]['work_code_complete'] = round($machine_device_data[$key]['count'] / $machine_device_data[$key]['work_code_qty'], 2);
        }

        //剩餘支數
        if (isset($machine_device_data[$key]['work_code_qty']) && isset($machine_device_data[$key]['count'])) {
            $work_code_remain_qty = $machine_device_data[$key]['work_code_qty'] - $machine_device_data[$key]['count'];
            if ($work_code_remain_qty < 0) {
                $work_code_remain_qty = 0;
            }
        }

        array_push($returnData['QueryTableData'], array(
            'product_line' => $params->group_name, //產線
            'device_name' => isset($machine_device_data[$key]['device_name']) ? $machine_device_data[$key]['device_name'] : '--', //機台名稱
            'now_status' => isset($machine_device_data[$key]['now_status']) ? $machine_device_data[$key]['now_status'] : '--', //狀態
            'speed' => isset($machine_device_data[$key]['speed']) ? $machine_device_data[$key]['speed'] : '--', //速度
            // 'count' => isset($machine_device_data[$key]['count']) ? $machine_device_data[$key]['count'] : '--',//目前支數
            'work_code_qty' => isset($machine_device_data[$key]['work_code_qty']) ? $machine_device_data[$key]['work_code_qty'] : '--', //目前工單需求支數
            // 'work_code_complete' => isset($machine_device_data[$key]['work_code_complete']) ? $machine_device_data[$key]['work_code_complete'] : '--',//當前工單完成率
            'workCode' => isset($machine_device_data[$key]['work_code']) ? $machine_device_data[$key]['work_code'] : '--', //當前工單
            // 'work_code_remain_qty' => isset($work_code_remain_qty) ? $work_code_remain_qty : '--',//剩餘支數
        ));
    }

    $returnData['Response'] = 'ok';
    $returnData['page'] = 'elecboard';
    return $returnData;
}

//回傳equal
function symbols_equal()
{
    return 'equal';
}

//回傳like
function symbols_like()
{
    return 'like';
}

//儲存機台編號
function get_device_array($machine_status_data)
{
    $device_array = [];
    foreach ($machine_status_data as $key => $value) {
        array_push($device_array, $value['device_name']);
    }
    return $device_array;
}

//儲存工單編號
function get_work_code_array($work_code_use_data)
{
    $work_code_array = [];
    foreach ($work_code_use_data as $key => $value) {
        if (!in_array($value['work_code'], $work_code_array)) {
            array_push($work_code_array, $value['work_code']);
        }
    }
    return $work_code_array;
}

//輾牙機台目前支數
function get_start_count($device_name, $wrok_code_start_time, $device_now_count)
{
    $whereAttr = new stdClass();
    $symbols = new stdClass();
    $whereAttr->upload_at = [$wrok_code_start_time];
    $symbols->upload_at = ['greater'];
    $data = array(
        'condition_1' => array(
            'table' => strtolower($device_name),
            'orderby' => ['asc', 'upload_at'],
            'limit' => [0, 1],
            'symbols' => $symbols,
            'where' => $whereAttr,
        )
    );
    $device_detail = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    if ($device_detail['Response'] !== 'ok') {
        return null;
    } else if (count($device_detail['QueryTableData']) == 0) {
        return null;
    }

    if (is_string($device_detail['QueryTableData'][0]['machine_detail'])) {
        $machine_detail_data = json_decode($device_detail['QueryTableData'][0]['machine_detail'], true);
    }

    if (!isset($machine_detail_data['cnt'])) {
        return null;
    }

    if (isset($device_now_count)) {
        $now_count = $device_now_count - $machine_detail_data['cnt'];
        if ($now_count >= 0) {
            return $now_count;
        } else {
            return null;
        }
    } else {
        return null;
    }
}


//demo用計數器
function DemoCounter($params)
{
    $process = $params->process;

    if ($process == '打頭') {
        $this_process = 5;
    } else if ($process == '輾牙') {
        $this_process = 6;
    }

    if ($this_process == 5) {
        $fields = ['device_name', 'machine_detail'];
        $data = array(
            'condition_1' => array(
                'fields' => $fields,
                'limit' => ["ALL"],
                'table' => 'machine_status_head'
            )
        );
        $machine_status_head = CommonSqlSyntax_Query($data, "MySQL");
        if ($machine_status_head['Response'] !== 'ok') {
            return $machine_status_head;
        } else if (count($machine_status_head['QueryTableData']) == 0) {
            $machine_status_head['Response'] = "no data";
            return $machine_status_head;
        }
        $machine_status_data = $machine_status_head['QueryTableData'];

        $returnData = [];
        $returnData['QueryTableData'] = [];

        foreach ($machine_status_data as $key => $value) {
            if (is_string($value['machine_detail'])) {
                $value['machine_detail'] = json_decode($value['machine_detail'], true);
            }

            if (isset($value['machine_detail']['cnt'])) {
                array_push($returnData['QueryTableData'], array(
                    'device_name' => $value['device_name'],
                    'count' => $value['machine_detail']['cnt']
                ));
            } else {
                array_push($returnData['QueryTableData'], array(
                    'device_name' => $value['device_name'],
                    'count' => '--'
                ));
            }
        }

        $returnData['Response'] = 'ok';
        $returnData['page'] = 'elecboard';
        return $returnData;
    } else if ($this_process == 6) {
        $fields = ['device_name', 'machine_detail', 'work_code'];
        $data = array(
            'condition_1' => array(
                'fields' => $fields,
                'limit' => ["ALL"],
                'table' => 'machine_status_thd'
            )
        );
        $machine_status_thd = CommonSqlSyntax_Query($data, "MySQL");
        if ($machine_status_thd['Response'] !== 'ok') {
            return $machine_status_thd;
        } else if (count($machine_status_thd['QueryTableData']) == 0) {
            $machine_status_thd['Response'] = "no data";
            return $machine_status_thd;
        }
        $machine_status_data = $machine_status_thd['QueryTableData'];

        $work_code_array = array_column($machine_status_data, 'work_code');

        if (!empty($work_code_array)) {
            //查詢工單上線數量
            $whereAttr = new stdClass();
            $whereAttr->work_code = $work_code_array;
            $whereAttr->project_id = ['6'];
            $whereAttr->status = ['S'];
            $symbols = new stdClass();
            $symbols->work_code = array_map('symbols_equal', $work_code_array);
            $symbols->project_id = ['equal'];
            $symbols->status = ['equal'];
            $data = array(
                'condition_1' => array(
                    'fields' => ['upload_at', 'work_code', 'project_id', 'device_name', 'status'],
                    'table' => 'work_code_use',
                    'orderby' => ['asc', 'upload_at'],
                    'limit' => ['ALL'],
                    'symbols' => $symbols,
                    'where' => $whereAttr,
                )
            );
            $work_code_use = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
            if ($work_code_use['Response'] !== 'ok') {
                return $work_code_use;
            }
            $work_code_use_data = $work_code_use['QueryTableData'];
        } else {
            $work_code_use_data = [];
        }

        $returnData = [];
        $returnData['QueryTableData'] = [];

        foreach ($machine_status_data as $key => $value) {
            if (is_string($value['machine_detail'])) {
                $value['machine_detail'] = json_decode($value['machine_detail'], true);
            }
            if ($value['work_code'] != '' && isset($value['machine_detail']['cnt'])) {
                foreach ($work_code_use_data as $work_code_use_data_key => $work_code_use_data_value) {
                    if ($value['work_code'] == $work_code_use_data_value['work_code'] && $value['device_name'] == $work_code_use_data_value['device_name']) {
                        $value['time'] = $work_code_use_data_value['upload_at'];
                    }
                }
                $device_now_count;
                if ($value['time'] != '') {
                    $device_now_count = get_start_count($value['device_name'], $value['time'], $value['machine_detail']['cnt']);
                }
                if (isset($device_now_count)) {
                    array_push($returnData['QueryTableData'], array(
                        'device_name' => $value['device_name'],
                        'count' => $device_now_count
                    ));
                } else {
                    array_push($returnData['QueryTableData'], array(
                        'device_name' => $value['device_name'],
                        'count' => '--'
                    ));
                }
            } else {
                array_push($returnData['QueryTableData'], array(
                    'device_name' => $value['device_name'],
                    'count' => '--'
                ));
            }
        }

        $returnData['Response'] = 'ok';
        $returnData['page'] = 'elecboard';
        return $returnData;
    }
}
