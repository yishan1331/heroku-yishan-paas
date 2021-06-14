<?php
function MainQuery($params)//主要查詢按鈕
{
    //回傳的資料
    $returnData['QueryTableData'] = [];

    $cus_id = $params->cusID;
    //查詢所有機台
    $device = CommonSpecificKeyQuery('Redis', $cus_id . '*', 'yes');
    if ($device['Response'] !== 'ok') {
        $returnData['Response'] = 'no data';
        $returnData['page'] = 'overview';
        return $returnData;
    }
    $device_data = $device['QueryValueData'];

    $all_device_data = array();
    $all_device_err_status = array();
    foreach ($device_data as $key => $value) {
        $operatelog_information = $value['operatelog_information'];
        if (!empty($operatelog_information)) {
            if (is_string($operatelog_information)) {
                $operatelog_information = json_decode($operatelog_information, true);
            }
            $time = $operatelog_information[count($operatelog_information) - 1]['endTime'];
            if ($value['machine_status'] == 'H') {
                $machine_erro_time = $operatelog_information[count($operatelog_information) - 1]['startTime'];
            }
        } else {
            $time = '-';
        }

        $category = $value['device_category'];

        $machine_abn_id = $value['machine_abn_id'];
        $machine_abn_description = $value['machine_abn_description'];
        if (!empty($machine_abn_id)) {
            if (is_string($machine_abn_id)) {
                $machine_abn_id = json_decode($machine_abn_id, true);
            }
        } else {
            $machine_abn_id = array();
        }
        if (!empty($machine_abn_description)) {
            if (is_string($machine_abn_description)) {
                $machine_abn_description = json_decode($machine_abn_description, true);
            }
        } else {
            $machine_abn_description = array();
        }
        if (!empty(strpos($value['machine_abn_id'], 'MC_0'))) {
            $new_machine_abn_id = array();
            $new_machine_abn_description = array();
            if (count($machine_abn_id) > 1) {
                foreach ($machine_abn_id as $machine_abn_key => $machine_abn_value) {
                    if (empty(strpos($$machine_abn_value, 'MC_0'))) {
                        array_push($new_machine_abn_id, $machine_abn_value);
                        array_push($new_machine_abn_description, $machine_abn_description[$machine_abn_key]);
                    }
                }
            }
            $machine_abn_id = $new_machine_abn_id;
            $machine_abn_description = $new_machine_abn_description;
        }

        $message = $category . $value['device_name'] . (!empty($machine_abn_description) ? '，' . implode("、", $machine_abn_description) : '') . '，' . $time;

        $all_device_data[$value['device_name']] = array(
            'device_id' => $value['device_id'],
            'device_name' => $value['device_name'],
            'device_category' => $category,
            'status' => empty($value['machine_status'])?'S':$value['machine_status'],
            'message' => $message
        );

        if ($value['machine_status'] == 'H') {
            array_push($all_device_err_status, array(
                'device_name' => $value['device_name'],
                'category' => $category,
                'machine_abn_id' => implode('、', $machine_abn_id),
                'machine_abn_description' => implode('、', $machine_abn_description),
                'machine_erro_time' => $machine_erro_time
            ));
        }
    }
    usort($all_device_data, 'sort_device_status');
    usort($all_device_err_status, 'sort_erro_time');

    array_push($returnData['QueryTableData'], array(
        'all_device_data' => $all_device_data,
        'err_status' => $all_device_err_status
    ));

    $returnData['Response'] = 'ok';

    return $returnData;
}

//機台狀態排序
function sort_device_status($a, $b){
    $status = array(
        'R' => 4,
        'Q' => 3,
        'H' => 2,
        'S' => 1,
        '' => 0,
    );
    if($status[$a['status']] == $status[$b['status']]) return 0;
    return ($status[$a['status']] > $status[$b['status']]) ? -1 : 1;
}

//異常時間排序
function sort_erro_time($a, $b){
    if(strtotime($a['machine_erro_time']) == strtotime($b['machine_erro_time'])) return 0;
    return (strtotime($a['machine_erro_time']) > strtotime($b['machine_erro_time'])) ? 1 : -1;
}