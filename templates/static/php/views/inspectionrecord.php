<?php
function MainQuery($params)
{
    $device_id = $params->deviceID;
    $sensor_list = get_sensor_list($device_id);
    $sensor_class = array();
    $sensor_class_record = array();
    foreach ($sensor_list as $key => $value) {
        $sensor_class_code = $value['sensor_class$sensor_class_code'];
        $sensor_class_name = $value['sensor_class$sensor_class_name'];
        if (!isset($sensor_class_record[$sensor_class_code])) {
            $sensor_class_record[$sensor_class_code] = $sensor_class_name;
            array_push($sensor_class, array(
                'sensor_class_code' => $sensor_class_code,
                'sensor_class_name' => $sensor_class_name,
                'device_id' => $device_id
            ));
        }
    }

    $returnData = array();
    $returnData['QueryTableData'] = $sensor_class;
    $returnData['Response'] = 'ok';
    return  $returnData;
}

function download_inspection_file($params)
{
    $selected_sensor = $params->selected_sensor;
    $device_id = $params->deviceID;
    $cus_id = $params->cusID;
    $selected_date = $params->selected_date;
    $end_time = explode(" ", $selected_date->endTime);
    $end_time = $end_time[0];
    $start_time = explode(" ", $selected_date->startTime);
    $start_time = $start_time[0];

    $sensor_class_list = get_sensor_class_list($device_id, $selected_sensor);
    $sensor_code_array = array();
    foreach ($sensor_class_list as $key => $value) {
        if (!isset($sensor_code_array[$value['sensor_class$sensor_class_code']])) {
            $sensor_code_array[$value['sensor_class$sensor_class_code']] = array(
                'sensor_code' => array(),
                'sensor_table_name' => $value['sensor_list$sensor_table_name'],
            );
        }
        array_push($sensor_code_array[$value['sensor_class$sensor_class_code']]['sensor_code'], $value['sensor_list$sensor_code']);
    }

    $file_name_array = array();
    foreach ($sensor_code_array as $key => $value) {
        if ($key == 'vibration') {
            $vibBearing_fields = array();
            $vibMotor_fields = array();
            foreach ($value['sensor_code'] as $sensor_code) {
                $bearing_data = explode("bearing_", $sensor_code);
                $motor_data = explode("motor_", $sensor_code);
                if (count($bearing_data) > 1) {
                    array_push($vibBearing_fields, $bearing_data[1]);
                }
                if (count($motor_data) > 1) {
                    array_push($vibMotor_fields, $motor_data[1]);
                }
            }

            //vibBearing
            if (!empty($vibBearing_fields)) {
                $file_name_vibBearing = $start_time . '~' . $end_time . 'vibBearing';
                array_push($vibBearing_fields, 'upload_at');
                $data = array(
                    'fields' => $vibBearing_fields,
                    'intervaltime' => array(
                        'upload_at' => [$selected_date->startTime,  $selected_date->endTime]
                    ),
                    'exportfilename' => $file_name_vibBearing
                );
                $inspection_result = ExportCsv($data, 'PostgreSQL', $cus_id . '_' . $device_id . '_vibBearing');
                if ($inspection_result['Response'] == 'ok') {
                    array_push($file_name_array, $file_name_vibBearing);
                }
            }
            
            //vibMotor
            if (!empty($vibMotor_fields)) {
                $file_name_vibMotor = $start_time . '~' . $end_time . 'vibMotor';
                array_push($vibMotor_fields, 'upload_at');
                $data = array(
                    'fields' => $vibMotor_fields,
                    'intervaltime' => array(
                        'upload_at' => [$selected_date->startTime,  $selected_date->endTime]
                    ),
                    'exportfilename' => $file_name_vibMotor
                );
                $inspection_result = ExportCsv($data, 'PostgreSQL', $cus_id . '_' . $device_id . '_vibMotor');
                if ($inspection_result['Response'] == 'ok') {
                    array_push($file_name_array, $file_name_vibMotor);
                }
            }
        } else {
            $file_name = $start_time . '~' . $end_time . $key;
            array_push($value['sensor_code'], 'upload_at');
            $data = array(
                'fields' =>  $value['sensor_code'],
                'intervaltime' => array(
                    'upload_at' => [$selected_date->startTime,  $selected_date->endTime]
                ),
                'exportfilename' =>  $file_name
            );
            $inspection_result = ExportCsv($data, 'PostgreSQL', $cus_id . '_' . $device_id . '_' . $value['sensor_table_name']);
            if ($inspection_result['Response'] == 'ok') {
                array_push($file_name_array, $file_name);
            }
        }
    }

    $returnData = array();
    $returnData['QueryTableData'] = $file_name_array;
    $returnData['Response'] = 'ok';
    return  $returnData;

    // // csv
    // $file_name = $start_time . '~' . $end_time . $selected_sensor[0];
    // if (is_file(dirname(__FILE__) . '/' . $file_name . 'csv')) {
    //     return $sensor_code_array;
    // } else {
    //     $data = array(
    //         'fields' =>  ['upload_at', ...$sensor_code_array],
    //         'intervaltime' => array(
    //             'upload_at' => [ $selected_date->startTime,  $selected_date->endTime]
    //         ),
    //         'exportfilename' => 'CUS01 ' . $file_name
    //     );
    //     $device = ExportCsv($data, 'PostgreSQL', 'test_main');
    //     echo json_encode($device);
    //     return;
    //     if ($device['Response'] !== 'ok') {
    //         return;
    //     }
    //     $this_device_data = $device['QueryValueData'];
    // }
}

function symbols_equal()
{
    return 'equal';
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

//機台感測點
function get_sensor_list($device_id)
{
    if (empty($device_id)) {
        return array();
    }

    $query_device_basic = new apiJsonBody_queryJoin;
    $query_device_basic->addFields('sensor_class', ['sensor_class_name', 'sensor_class_code']);
    $query_device_basic->setTables(['device_basic', 'machine_sensor_list', 'sensor_list', 'sensor_class']);
    $join = new stdClass();
    $join->device_basic = [];
    $machine_sensor_list = new stdClass();
    $machine_sensor_list->machine_sensor_list = new stdClass();
    $machine_sensor_list->machine_sensor_list->id = new stdClass();
    $machine_sensor_list->machine_sensor_list->id = "device_id";
    $machine_sensor_list->machine_sensor_list->JOIN = new stdClass();
    $machine_sensor_list->machine_sensor_list->JOIN->sensor_list = new stdClass();
    $machine_sensor_list->machine_sensor_list->JOIN->sensor_list->sensor_id = new stdClass();
    $machine_sensor_list->machine_sensor_list->JOIN->sensor_list->sensor_id = "id";
    $machine_sensor_list->machine_sensor_list->JOIN->sensor_list->JOIN = new stdClass();
    $machine_sensor_list->machine_sensor_list->JOIN->sensor_list->JOIN->sensor_class = new stdClass();
    $machine_sensor_list->machine_sensor_list->JOIN->sensor_list->JOIN->sensor_class->sensor_class_code = new stdClass();
    $machine_sensor_list->machine_sensor_list->JOIN->sensor_list->JOIN->sensor_class->sensor_class_code = "sensor_class_code";
    array_push($join->device_basic, $machine_sensor_list);
    $query_device_basic->setJoin($join);
    $query_device_basic->addJointype('device_basic', 'machine_sensor_list', 'inner');
    $query_device_basic->addJointype('machine_sensor_list', 'sensor_list', 'inner');
    $query_device_basic->addJointype('sensor_list', 'sensor_class', 'inner');
    $query_device_basic->addSymbols('device_basic', 'id', 'equal');
    $query_device_basic->addWhere('device_basic', 'id', $device_id);
    $query_device_basic->addSymbols('machine_sensor_list', 'sensor_enable', 'equal');
    $query_device_basic->addWhere('machine_sensor_list', 'sensor_enable', 'Y');
    $query_device_basic->setLimit([0,99999]);
    $query_device_basic_data = $query_device_basic->getApiJsonBody();
    $device_basic = CommonSqlSyntaxJoin_Query($query_device_basic_data, "MySQL", "no");
    if ($device_basic['Response'] !== 'ok') {
        $device_basic_data = [];
    } else {
        $device_basic_data = $device_basic['QueryTableData'];
    }
        
    return $device_basic_data;
}

//機台感測點
function get_sensor_class_list($device_id, $selected_sensor)
{
    if (empty($device_id)) {
        return array();
    }

    $query_device_basic = new apiJsonBody_queryJoin;
    $query_device_basic->addFields('sensor_list', ['sensor_name', 'sensor_code', 'sensor_table_name']);
    $query_device_basic->addFields('sensor_class', ['sensor_class_code']);
    $query_device_basic->setTables(['device_basic', 'machine_sensor_list', 'sensor_list', 'sensor_class']);
    $join = new stdClass();
    $join->device_basic = [];
    $machine_sensor_list = new stdClass();
    $machine_sensor_list->machine_sensor_list = new stdClass();
    $machine_sensor_list->machine_sensor_list->id = new stdClass();
    $machine_sensor_list->machine_sensor_list->id = "device_id";
    $machine_sensor_list->machine_sensor_list->JOIN = new stdClass();
    $machine_sensor_list->machine_sensor_list->JOIN->sensor_list = new stdClass();
    $machine_sensor_list->machine_sensor_list->JOIN->sensor_list->sensor_id = new stdClass();
    $machine_sensor_list->machine_sensor_list->JOIN->sensor_list->sensor_id = "id";
    $machine_sensor_list->machine_sensor_list->JOIN->sensor_list->JOIN = new stdClass();
    $machine_sensor_list->machine_sensor_list->JOIN->sensor_list->JOIN->sensor_class = new stdClass();
    $machine_sensor_list->machine_sensor_list->JOIN->sensor_list->JOIN->sensor_class->sensor_class_code = new stdClass();
    $machine_sensor_list->machine_sensor_list->JOIN->sensor_list->JOIN->sensor_class->sensor_class_code = "sensor_class_code";
    array_push($join->device_basic, $machine_sensor_list);
    $query_device_basic->setJoin($join);
    $query_device_basic->addJointype('device_basic', 'machine_sensor_list', 'inner');
    $query_device_basic->addJointype('machine_sensor_list', 'sensor_list', 'inner');
    $query_device_basic->addJointype('sensor_list', 'sensor_class', 'inner');
    $query_device_basic->addSymbols('device_basic', 'id', 'equal');
    $query_device_basic->addWhere('device_basic', 'id', $device_id);
    $query_device_basic->addSymbols('machine_sensor_list', 'sensor_enable', 'equal');
    $query_device_basic->addWhere('machine_sensor_list', 'sensor_enable', 'Y');
    $query_device_basic->addSymbols('sensor_class', 'sensor_class_code', 'in');
    $query_device_basic->addWhere('sensor_class', 'sensor_class_code', $selected_sensor);
    $query_device_basic->setLimit([0,99999]);
    $query_device_basic_data = $query_device_basic->getApiJsonBody();
    $device_basic = CommonSqlSyntaxJoin_Query($query_device_basic_data, "MySQL", "no");
    if ($device_basic['Response'] !== 'ok') {
        $device_basic_data = [];
    } else {
        $device_basic_data = $device_basic['QueryTableData'];
    }
        
    return $device_basic_data;
}