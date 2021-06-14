<?php
function MainQuery($params)//主要查詢按鈕
{
    $test = CommonTableQuery('MySQL', 'device_basic');
    if ($test['Response'] !== 'ok') {
        return;
    }
    $test_data = $test;
    return $test_data;
};

function settingUpdate($params)
{
    $data = array(
        'sensor_error' => [json_encode($params->data_sensor_err)],
        'sensor_warn' => [json_encode($params->data_sensor_warn)],
        'old_device_name' => [$params->device_name]
    );
    return CommonUpdate($data, 'MySQL', 'device_basic');
};
