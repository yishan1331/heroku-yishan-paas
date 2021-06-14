<?php
function MainQuery()
{
}
function query_cus_list()//查詢客戶清單
{   
    $data = array(
        'col' => 'delete_enable',
        'valueStart' => 'N',
        'valueEnd' => 'N'
    );
    $query_customer = CommonIntervalQuery($data, 'MySQL', 'customer');
    if ($query_customer['Response'] !== 'ok') {
        return array(
            'Response' => "no data"
        );
    }
    $customer_data = $query_customer['QueryTableData'];
    $return_customer_data = array();
    foreach ($customer_data as $value) {
        $data_obj = array(
            'text' => $value['id'] . " " . $value['cus_name'],
            'value' => $value['id']
        );
        array_push($return_customer_data, $data_obj);
    }
    $return_data = array(
        'customer_data' => $return_customer_data,
        'Response' => "ok"
    );
    return $return_data;
}
