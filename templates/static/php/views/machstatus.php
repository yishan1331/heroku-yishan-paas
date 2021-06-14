<?php
date_default_timezone_set('Asia/Taipei');
function MainQuery($params)//主要查詢按鈕
{
    $now_time = strtotime(date("Y-m-d H:i:s"));
    // 紀錄時間區間
    if ($now_time > strtotime(date("Y-m-d 08:00:00"))) {
        $time_interval = array(
            'start' => date("Y-m-d 08:00:00"),
            'end' => date("Y-m-d H:i:s", strtotime(date('Y-m-d 08:00:00'))+86400)
        );
    } else {
        $time_interval = array(
            'start' => date("Y-m-d H:i:s", strtotime(date('Y-m-d 08:00:00'))-86400),
            'end' => date("Y-m-d 08:00:00")
        );
    }
    
    // 查詢machine_status，機台當前狀態
    // 查詢機台機型
    // 機台名稱、目前工單編號、是否有首件檢查1=有，機台運作狀態、機台狀態Q=非故障
    $fields = ['device_name', 'work_code', 'scroll_no', 'first_inspection', 'machine_detail', 'mac_status'];
    $data = array(
        'condition_1' => array(
            'table' => 'machine_status_head',
            'fields' => $fields,
            'limit' => ["ALL"]
        )
    );
    $machine_status_head = CommonSqlSyntax_Query($data, "MySQL");
    if ($machine_status_head['Response'] !== 'ok') {
        $machine_status_head['page'] = 'machstatus';
        return $machine_status_head;
    } else if (count($machine_status_head['QueryTableData']) == 0) {
        $machine_status_head['page'] = 'machstatus';
        $machine_status_head['Response'] = "no data";
        return $machine_status_head;
    }
    $machine_status_head_data = $machine_status_head['QueryTableData'];
    
    //用該值來儲存資料
    $machine_device_data = $machine_status_head_data;

    //查詢machine_abn，機台異常資料
    $machine_abn = CommonTableQuery('MySQL', 'machine_abn');
    if ($machine_abn['Response'] !== 'ok') {
        $machine_abn['page'] = 'machstatus';
        return $machine_abn;
    } else if (count($machine_abn['QueryTableData']) == 0) {
        $machine_abn['page'] = 'machstatus';
        $machine_abn['Response'] = "no data";
        return $machine_abn;
    }
    $machine_abn_data = $machine_abn['QueryTableData'];
    $machine_abn_code = [];
    for ($i=0; $i < count($machine_abn_data); $i++) { 
        $machine_abn_code[$machine_abn_data[$i]['name']] = array(
            'err_code' => $machine_abn_data[$i]['err_code'],
            'value' => $machine_abn_data[$i]['value']
        );
    }
    
    //儲存機台編號
    $device_name = [];
    $device_name_symbols = [];
    $on_wire_code = array('where' => array('scroll_no' => []), 'symbols' => array('scroll_no' => []));
    $device_status = [];
    for ($i=0; $i < count($machine_device_data); $i++) {
        //將數值轉字串
        array_push($device_name, "" . $machine_device_data[$i]['device_name']);
        array_push($device_name_symbols, "equal");

        //查詢線材支架重
        if ($machine_device_data[$i]['scroll_no'] != "" ) {
            array_push($on_wire_code['where']['scroll_no'], $machine_device_data[$i]['scroll_no']);
            array_push($on_wire_code['symbols']['scroll_no'], 'equal');
        }

        $data = array(
            'col' => 'upload_at',
            'valueStart' => $time_interval['start'],
            'valueEnd' => date("Y-m-d H:i:s", $now_time)
        );
        $this_device_status = CommonIntervalQuery($data, "PostgreSQL", strtolower($machine_device_data[$i]['device_name']));

        if ($this_device_status['Response'] == 'ok' && count($this_device_status['QueryTableData']) != 0) {
            $device_status[$machine_device_data[$i]['device_name']] = $this_device_status['QueryTableData'];
        }
    }

    //查詢線材支架重
    if (!empty($on_wire_code['where']['scroll_no'])) {
        $data = array(
            'condition_1' => array(
                'table' => 'wire_stack',
                'fields' => ['scroll_no', 'rack_wgt'],
                'where' => $on_wire_code['where']['scroll_no'],
                'limit' => ['ALL'],
                'symbols' => $on_wire_code['symbols']['scroll_no']
            )
        );
    }
    $wire_stack = CommonSqlSyntax_Query($data, "MsSQL");
    if ($wire_stack['Response'] !== 'ok' || count($wire_stack['QueryTableData']) == 0) {
        $wire_stack_data = [];
    } else {
        $wire_stack_data = $wire_stack_data['QueryTableData'];
    }

    // 查詢機台機型
    $whereAttr = new stdClass();
    $whereAttr->name = [$device_name];
    $symbols = new stdClass();
    $symbols->name = [$device_name_symbols];
    $data = array(
        'condition_1' => array(
            'table' => 'device_box',
            'limit' => ["ALL"],
            'where' => $whereAttr,
            'symbols' => $symbols,
        )
    );
    $device_box = CommonSqlSyntax_Query($data, "MsSQL");
    if ($device_box['Response'] !== 'ok' || count($device_box['QueryTableData']) == 0) {
        $device_box_data = [];
    } else {
        $device_box_data = $device_box['QueryTableData'];
    }

    //查詢時間內有上/下線的工單
    $whereAttr = new stdClass();
    $whereAttr->device_name = [$device_name];
    $symbols = new stdClass();
    $symbols->device_name = [$device_name_symbols];
    $intervaltime = array(
        'upload_at' => array(array($time_interval['start'], $time_interval['end']))
    );
    $data = array(
        'condition_1' => array(
            'table' => 'work_code_use',
            'intervaltime' => $intervaltime,
            'limit' => ["ALL"],
            'where' => $whereAttr,
            'symbols' => $symbols,
            'orderby' => ['asc','upload_at']
        )
    );
    $work_code_use = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    if ($work_code_use['Response'] !== 'ok' || count($work_code_use['QueryTableData']) == 0) {
        $work_code_use_data = [];
    } else {
        $work_code_use_data = $work_code_use['QueryTableData'];
    }

    //整理工單
    $machine_work_code = [];
    $work_code = [];
    for ($i=0; $i < count($work_code_use_data); $i++) { 
        //判斷該工單是否已經紀錄
        if (!in_array($work_code_use_data[$i]['work_code'], $work_code)) {
            array_push($work_code, $work_code_use_data[$i]['work_code']);
        }
        //紀錄為某機台的工單
        if (!isset($machine_work_code[$work_code_use_data[$i]['device_name']])) {
            $machine_work_code[$work_code_use_data[$i]['device_name']] = [];
        } 
        //紀錄為某工單的開始時間
        if (!isset($machine_work_code[$work_code_use_data[$i]['device_name']][$work_code_use_data[$i]['work_code']])) {
            $machine_work_code[$work_code_use_data[$i]['device_name']][$work_code_use_data[$i]['work_code']] = array(
                'S' => [],
                'E' => []
            );
        } 
        if ($work_code_use_data[$i]['status'] == 'E') {
            if(count($machine_work_code[$work_code_use_data[$i]['device_name']][$work_code_use_data[$i]['work_code']]['S']) == count($machine_work_code[$work_code_use_data[$i]['device_name']][$work_code_use_data[$i]['work_code']]['E'])) {
                array_push($machine_work_code[$work_code_use_data[$i]['device_name']][$work_code_use_data[$i]['work_code']]['S'], $time_interval['start']);
            }
        }
        array_push($machine_work_code[$work_code_use_data[$i]['device_name']][$work_code_use_data[$i]['work_code']][$work_code_use_data[$i]['status']], $work_code_use_data[$i]['upload_at']);
    }

    //查詢工單的單支重
    $fields = new stdClass();
    $fields->work_order = ["code", "status"];
    $fields->commodity = ["material_weight" ,"standard_weight"];//material_weight需要改成梅花塊，標準單支+梅花塊=原料重量，若梅花塊=0，則標準單支*1.15=原料重量
    $join = new stdClass();
    $join->work_order = [];
    $commodity = new stdClass();
    $commodity->commodity = new stdClass();
    $commodity->commodity->commodity_code = new stdClass();
    $commodity->commodity->commodity_code = "code";
    array_push($join->work_order, $commodity);
    $tables = ['work_order', 'commodity'];
    $whereAttr = new stdClass();
    $whereAttr->work_order = new stdClass();
    $whereAttr->work_order->code = $work_code;
    $whereAttr->work_order->status = ['1', 'E'];
    $symbols = new stdClass();
    $symbols->work_order = new stdClass();
    $symbols->work_order->code = [];
    $symbols->work_order->status = ['equal', 'equal'];
    $i = 0;
    while ($i < count($work_code)) {
        array_push($symbols->work_order->code, 'equal');
        $i++;
    }
    $tables = ['work_order', 'commodity'];
    $jointype = new stdClass();
    $jointype->work_order_commodity= "inner";
    $data = array(
        'condition_1' => array(
            'fields' => $fields,
            'join' => $join,
            'jointype' => $jointype,
            'tables' => $tables,
            'limit' => [0,count($work_code)],
            'where' => $whereAttr,
            'symbols' => $symbols
        )
    );
    $work_order = CommonSqlSyntaxJoin_Query($data, "MsSQL");
    if ($work_order['Response'] !== 'ok' || count($work_order['QueryTableData']) == 0) {
        $work_order_data = [];
    } else {
        $work_order_data = $work_order['QueryTableData'];
    }

    //已完工的工單
    $finished_work_code = [];
    // $erro_work_code = [];
    for ($i=0; $i < count($work_order_data); $i++) { 
        array_push($finished_work_code, $work_order_data[$i]['work_order$code']);
    }

    $whereAttr = new stdClass();
    $whereAttr->work_code = [$work_code];
    $symbols = new stdClass();
    $symbols->work_code = ["equal"];
    $data = array(
        'condition_1' => array(
            'table' => 'wire_scroll_no_use',
            'limit' => ["ALL"],
            'where' => $whereAttr,
            'symbols' => $symbols,
            'orderby' => ['asc','upload_at']
        )
    );
    $wire_scroll_no_use = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    if ($wire_scroll_no_use['Response'] !== 'ok' || count($wire_scroll_no_use['QueryTableData']) == 0) {
        $wire_scroll_no_use_data = [];
    } else {
        $wire_scroll_no_use_data = $wire_scroll_no_use['QueryTableData'];
    }

    //查詢工單的所有桶重
    $runcard_data = [];
    for ($i=0; $i < count($work_code); $i++) { 
        $whereAttr = new stdClass();
        $whereAttr->runcard_code = [$work_code[$i]];
        $whereAttr->project_id = [5];
        $whereAttr->identify = [1];
        $symbols = new stdClass();
        $symbols->runcard_code = ["like"];
        $symbols->project_id = ["equal"];
        $symbols->identify = ["equal"];
        $data = array(
            'condition_1' => array(
                'table' => 'runcard',
                'fields' => ["upload_at", "runcard_code", "screw_weight"],
                'limit' => ["ALL"],
                'where' => $whereAttr,
                'symbols' => $symbols,
                'orderby' => ['asc','upload_at']
            )
        );
        $runcard = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
        if (isset($runcard['QueryTableData'])) {
            $runcard_data = array_merge($runcard_data, $runcard['QueryTableData']);
        }
    }

    //查詢machine_on_off_hist，機台開關機時間
    $intervaltime = array(
        'upload_at' => array(array($time_interval['start'], $time_interval['end']))
    );
    $whereAttr = new stdClass();
    $whereAttr->device_name = [array_map('strtolower', $device_name)];
    $symbols = new stdClass();
    $symbols->device_name = [$device_name_symbols];
    $data = array(
        'condition_1' => array(
            'table' => 'machine_on_off_hist',
            'intervaltime' => $intervaltime,
            'limit' => ["ALL"],
            'where' => $whereAttr,
            'symbols' => $symbols,
            'orderby' => ['asc','upload_at']
        )
    );
    $machine_on_off_hist = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    if ($machine_on_off_hist['Response'] !== 'ok') {
        $machine_on_off_hist['page'] = 'machstatus';
        return $machine_on_off_hist;
    } else if (count($machine_on_off_hist['QueryTableData']) == 0) {
        $machine_on_off_hist['Response'] = "no data";
        // return $machine_on_off_hist;
    }
    $machine_on_off_hist_data = $machine_on_off_hist['QueryTableData'];

    //判斷機台是否正在開機
    $machine_device_status = [];
    for ($i=0; $i < count($machine_on_off_hist_data); $i++) { 
        if (!isset($machine_device_status[strtoupper($machine_on_off_hist_data[$i]['device_name'])])) {
            $machine_device_status[strtoupper($machine_on_off_hist_data[$i]['device_name'])]=[];
            if ($machine_on_off_hist_data[$i]['status'] == 'S') {
                array_push($machine_device_status[strtoupper($machine_on_off_hist_data[$i]['device_name'])], array($machine_on_off_hist_data[$i]['upload_at']));
            } else if ($machine_on_off_hist_data[$i]['status'] == 'E') {
                if (strtotime($machine_on_off_hist_data[$i]['upload_at']) > strtotime(date("Y-m-d 08:00:00"))) {
                    array_push($machine_device_status[strtoupper($machine_on_off_hist_data[$i]['device_name'])], array(date("Y-m-d 08:00:00"), $machine_on_off_hist_data[$i]['upload_at']));
                } else {
                    array_push($machine_device_status[strtoupper($machine_on_off_hist_data[$i]['device_name'])], array(date("Y-m-d H:i:s", strtotime(date('Y-m-d 08:00:00'))-86400), $machine_on_off_hist_data[$i]['upload_at']));
                }
            }
        } else {
            if ($machine_on_off_hist_data[$i]['status'] == 'S') {
                array_push($machine_device_status[strtoupper($machine_on_off_hist_data[$i]['device_name'])], array($machine_on_off_hist_data[$i]['upload_at']));
            } else if ($machine_on_off_hist_data[$i]['status'] == 'E') {
                array_push($machine_device_status[strtoupper($machine_on_off_hist_data[$i]['device_name'])][count($machine_device_status[strtoupper($machine_on_off_hist_data[$i]['device_name'])])-1], $machine_on_off_hist_data[$i]['upload_at']);
            }
        }
    }
    for ($i=0; $i < count($device_name); $i++) { 
        if (!isset($machine_device_status[$device_name[$i]])) {
            //查詢machine_on_off_hist，機台開關機時間
            $symbols = new stdClass();
            $symbols->device_name = ['equal'];
            $whereAttr = new stdClass();
            $whereAttr->device_name = [strtolower($device_name[$i])];
            $data = array(
                'condition_1' => array(
                    'table' => 'machine_on_off_hist',
                    'limit' => [0,1],
                    'where' => $whereAttr,
                    'symbols' => $symbols,
                    'orderby' => ['desc','upload_at']
                )
            );
            $this_machine_on_off_hist = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
            if ($this_machine_on_off_hist['Response'] == 'ok' && count($this_machine_on_off_hist['QueryTableData']) != 0) {
                $this_machine_on_off_hist_data = $this_machine_on_off_hist['QueryTableData'];
                $machine_device_status[strtoupper($this_machine_on_off_hist_data[0]['device_name'])]=[];
                if ($this_machine_on_off_hist_data[0]['status'] == 'S') {
                    if (strtotime($this_machine_on_off_hist_data[0]['upload_at']) < strtotime(date("Y-m-d 08:00:00"))) {
                        array_push($machine_device_status[strtoupper($this_machine_on_off_hist_data[0]['device_name'])], array(date("Y-m-d 08:00:00")));
                    } else {
                        array_push($machine_device_status[strtoupper($this_machine_on_off_hist_data[0]['device_name'])], array($this_machine_on_off_hist_data[0]['upload_at']));
                    }
                }
            }
        }
    }

    //記錄機台運轉時間
    $machine_OPR_time = [];
    //記錄該機台桶重
    $machine_work_code_runcard = [];
    //整理實際耗用線材重量            
    $machine_work_code_use_wire = [];
    //整理實際工單耗用線材重量
    $machine_work_code_use_wire_weight = [];
    //紀錄機台狀態
    $device_status_data = [];
    //紀錄機台稼動率
    $device_activation_data = [];
    foreach ($machine_work_code as $machine_device_name => $machine_work_code_obj) {
        //初始化新增陣列
        if (!isset($machine_OPR_time[$machine_device_name])) {
            $machine_OPR_time[$machine_device_name] = [];
            $machine_work_code_runcard[$machine_device_name] = [];
            $machine_work_code_use_wire[$machine_device_name] = [];
            $machine_work_code_use_wire_weight[$machine_device_name] = [];
        }
        $inspection_work_code = [];
        foreach ($machine_work_code_obj as $machine_work_code_value => $machine_work_code_time) {
            //取末桶時間
            for ($i=count($runcard_data)-1; $i >= 0; $i--) { 
                $runcard_code = explode("-", $runcard_data[$i]['runcard_code']);
                if (!isset($machine_work_code_runcard[$machine_device_name][$machine_work_code_value])) {
                    $machine_work_code_runcard[$machine_device_name][$machine_work_code_value] = 0;
                }
                //確認是同一張工單
                if ($machine_work_code_value == $runcard_code[0]) {
                    //確認時間軸，確保是在上線後的首件檢查
                    foreach ($machine_work_code_time['S'] as $machine_work_code_time_index => $machine_work_code_time_S) {
                        if (!isset($machine_work_code_time['E'][$machine_work_code_time_index])) {
                        break;
                        }
                        //確認末桶時間小於下線時間
                        if (strtotime($runcard_data[$i]['upload_at']) <= strtotime($machine_work_code_time['E'][$machine_work_code_time_index])) {                            
                            //確認是已經完工的工單，再進行桶數的加總，尚未完工的將判斷為現有時間
                            if (in_array($runcard_code[0], $finished_work_code)) {
                                //桶重加總
                                $machine_work_code_runcard[$machine_device_name][$machine_work_code_value] += $runcard_data[$i]['screw_weight'];
                            }
                        }
                    }
                }
            }

            //紀錄各工單使用線材重量
            for ($j=0; $j < count($wire_scroll_no_use_data); $j++) { 
                if (in_array($wire_scroll_no_use_data[$j]['work_code'], $finished_work_code) && $wire_scroll_no_use_data[$j]['work_code'] == $machine_work_code_value) {
                    if (!isset($machine_work_code_use_wire[$machine_device_name][$machine_work_code_value])) {
                        $machine_work_code_use_wire[$machine_device_name][$machine_work_code_value] = [];
                    }
                    if (!isset($machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']])) {
                        $machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']] = [];
                    }
                    if ($wire_scroll_no_use_data[$j]['status'] == "S") {
                        if (!isset($machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['S'])) {
                            $machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['S'] = [];
                        }
                        array_push($machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['S'], $wire_scroll_no_use_data[$j]['weight']);
                    } else {
                        if (!isset($machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['E'])) {
                            $machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['E'] = [];
                        }
                        array_push($machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['E'], $wire_scroll_no_use_data[$j]['weight']);

                        if (count($machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['S']) ==
                        count($machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['E'])) 
                        {
                            if (!isset($machine_work_code_use_wire_weight[$machine_device_name][$machine_work_code_value])) {
                                $machine_work_code_use_wire_weight[$machine_device_name][$machine_work_code_value] = 0;
                            }
                            $machine_work_code_use_wire_weight[$machine_device_name][$machine_work_code_value] += $machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['S'][count($machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['S']) - 1] - $machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['E'][count($machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['E']) - 1];
                        } else if (count($machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['S']) <
                        count($machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['E'])) {
                            //查詢該線材的上限重量
                            $symbols = new stdClass();
                            $symbols->work_code = ['equal'];
                            $symbols->scroll_no = ['equal'];
                            $symbols->status = ['equal'];
                            $symbols->upload_at = ["greater"];
                            $whereAttr = new stdClass();
                            $whereAttr->work_code = [$machine_work_code_value];
                            $whereAttr->scroll_no = [$wire_scroll_no_use_data[$j]['scroll_no']];
                            $whereAttr->status = ['E'];
                            $whereAttr->upload_at = [$wire_scroll_no_use_data[$j]['upload_at']];
                            $data = array(
                                'condition_1' => array(
                                    'table' => 'wire_scroll_no_use',
                                    'limit' => [0,1],
                                    'where' => $whereAttr,
                                    'symbols' => $symbols,
                                    'orderby' => ['desc','upload_at']
                                )
                            );
                            $this_wire_scroll_no = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
                            if ($this_wire_scroll_no['Response'] !== 'ok' || count($this_wire_scroll_no['QueryTableData']) == 0) {
                                $this_wire_scroll_no_data = [];
                            } else {
                                $this_wire_scroll_no_data = $this_wire_scroll_no['QueryTableData'];
                            }

                            if (count($this_wire_scroll_no_data) > 0) {
                                array_push($machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['S'], $this_wire_scroll_no_data[0]['weight']);
                                $machine_work_code_use_wire_weight[$machine_device_name][$machine_work_code_value] += $machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['S'][count($machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['S']) - 1] - $machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['E'][count($machine_work_code_use_wire[$machine_device_name][$machine_work_code_value][$wire_scroll_no_use_data[$j]['scroll_no']]['E']) - 1];
                            }
                        }
                    }
                }
            }
        }

        // 查看總日、時
        // $date = floor($stop_time / 86400);
        // $hour = floor($stop_time % 86400 / 3600);
        // $minute = floor($stop_time % 86400 / 60) - $hour * 60;
        // $second = floor($stop_time % 86400 % 60);
        // $date < 10 ? $showDate = '0' . $date : $showDate = $date;
        // $hour < 10 ? $showHour = '0' . $hour : $showHour = $hour;
        // $minute < 10 ? $showMinute = '0' . $minute : $showMinute = $minute;
        // $second < 10 ? $showSecond = '0' . $second : $showSecond = $second;
        // $totalTime = $showDate . " " . $showHour . ":" . $showMinute . ":" . $showSecond;
        // echo $totalTime;
    }
    foreach ($device_status as $device_status_name => $device_status_detail) {
        $machine_OPR_time[$device_status_name] = array('data_log' => [], 'data' => 0);

        $device_status_data[$device_status_name]['data'] = [];
        $device_status_data[$device_status_name]['data'] = $device_status_detail;
        $device_status_data[$device_status_name]['detail'] = [];

        $machine_detail_old_Data = [];
        $machine_detail_now_Detail = [];
        $machine_detail_now_Status = [];
        $machine_detail_now_Status_Time = [];
        for ($j=0; $j < count($device_status_data[$device_status_name]['data']); $j++) { 
            $machine_detail = $device_status_data[$device_status_name]['data'][$j]['machine_detail'];
            $chain_this_data = array();
            foreach ($machine_light_abn_data as $key => $value) {
                $chain_this_data[$key] = $machine_detail[$key];
            }
            if (isset($machine_detail['OPR'])) {
                $chain_this_data['OPR'] = $machine_detail['OPR'];
            } else {
                $chain_this_data['OPR'] = 0;
            }
            // $chain_this_data = array(
            //     'fnt_sf_pin' => $machine_detail['fnt_sf_pin'],
            //     'len_short' => $machine_detail['len_short'],
            //     'bk_sf_pin' => $machine_detail['bk_sf_pin'],
            //     'air_press_light' => $machine_detail['air_press_light'],
            //     'in_lube' => $machine_detail['in_lube'],
            //     'overload' => $machine_detail['overload'],
            //     'pwr_light' => $machine_detail['pwr_light'],
            //     'mtr_end' => $machine_detail['mtr_end'],
            //     'end_lube_press' => $machine_detail['end_lube_press'],
            //     'sf_door' => $machine_detail['sf_door'],
            //     'lube_overflow' => $machine_detail['lube_overflow'],
            //     'tab_float' => $machine_detail['tab_float'],
            //     'inv_abn' => $machine_detail['inv_abn'],
            //     'finish_cnt' => $machine_detail['finish_cnt'],
            //     'OPR' => $machine_detail['OPR'],
            // );

            if ($j == 0) {
                $machine_detail_old_Data = $chain_this_data;//儲存當作比對的物件
                $machine_detail_now_Status = $chain_this_data;//儲存現在的物件
                array_push($machine_detail_now_Status_Time, $machine_detail['timestamp']);//第一筆為開始，第二筆為結束
            } else {
                if ($j < count($device_status_data[$device_status_name]['data']) - 1) {//確認不是最後一筆
                    if (count(array_keys(array_diff_assoc($chain_this_data, $machine_detail_old_Data))) == 0) {//判斷是否一樣，如果一樣就儲存最後的時間
                        $machine_detail_now_Status = $machine_detail_old_Data;
                        $machine_detail_now_Status_Time[1] = $machine_detail['timestamp'];
                    } else {//如果不一樣，儲存最後的時間，並記錄到陣列中，在開始一筆新的紀錄
                        //如果判斷的是潤滑中再改變其餘皆正常，則視為相同狀態
                        if (count(array_keys(array_diff_assoc($chain_this_data, $machine_detail_old_Data))) == 1 && array_keys(array_diff_assoc($chain_this_data, $machine_detail_old_Data))[0] == 'in_lube') {
                            if ($chain_this_data['OPR'] == 0 && $machine_detail_old_Data['OPR'] == 0) {
                                $machine_detail_now_Status = $machine_detail_old_Data;
                                $machine_detail_now_Status_Time[1] = $machine_detail['timestamp'];//時間異常，暫時用server時間
                                continue;
                            }
                        }
                        $machine_detail_now_Status = $machine_detail_old_Data;
                        $machine_detail_now_Status_Time[1] = $machine_detail['timestamp'];
                        $machine_detail_now_Detail[count($machine_detail_now_Detail)] = $machine_detail_now_Status;
                        $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['startTime'] = $machine_detail_now_Status_Time[0];
                        $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['endTime'] = $machine_detail_now_Status_Time[1];
                        $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['cnt'] = $machine_detail['cnt'];
                     
                        $machine_detail_old_Data = $chain_this_data;
                        $machine_detail_now_Status = $machine_detail_old_Data;
                        $machine_detail_now_Status_Time = [];
                        array_push($machine_detail_now_Status_Time, $machine_detail['timestamp']);
                    }
                } else {//最後一筆，儲存最後的時間，並記錄到陣列中
                    $machine_detail_now_Status = $machine_detail_old_Data;
                    $machine_detail_now_Status_Time[1] = $machine_detail['timestamp'];
                    $machine_detail_now_Detail[count($machine_detail_now_Detail)] = $machine_detail_now_Status;
                    $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['startTime'] = $machine_detail_now_Status_Time[0];
                    $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['endTime'] = $machine_detail_now_Status_Time[1];
                    $machine_detail_now_Detail[count($machine_detail_now_Detail) - 1]['cnt'] = $machine_detail['cnt'];
                }
            }
        }
        $device_status_data[$device_status_name]['detail'] = $machine_detail_now_Detail;
        //紀錄運轉時段
        if(count($device_status_data[$device_status_name]['detail']) > 0) {
            for ($j=0; $j < count($device_status_data[$device_status_name]['detail']); $j++) { 
                $status_detail = $device_status_data[$device_status_name]['detail'][$j];

                if ($status_detail['OPR'] == 1) {
                    array_push($machine_OPR_time[$device_status_name]['data_log'], array('endTime' => $status_detail['endTime'], 'startTime' => $status_detail['startTime']));
                    $machine_OPR_time[$device_status_name]['data'] += strtotime($status_detail['endTime']) - strtotime($status_detail['startTime']);
                }
            }
        }
        //計算稼動率
        //若為0則代表無運轉時間
        if ($machine_OPR_time[$device_status_name]['data'] == 0) {
            $device_activation_data[$device_status_name] = 0;
        } else {
            //若不為0則將運轉時間/(目前時間-當日開始時間)
            $device_activation_data[$device_status_name] = round(round($machine_OPR_time[$device_status_name]['data'] / ($now_time - strtotime($time_interval['start'])), 4) * 100, 2);
        }
    }

    //加入機台型號、機台狀態
    for ($i=0; $i < count($machine_device_data); $i++) {
        //加入機台的型號
        if(count($device_box_data) > 0) {
            for ($j=0; $j < count($device_box_data); $j++) { 
                if ($machine_device_data[$i]['device_name'] == $device_box_data[$j]['name']) {
                    $machine_device_data[$i]['model'] = $device_box_data[$j]['model'];
                break;
                }
            }
        }
        //判斷機台狀態
        if (!isset($machine_device_status[$machine_device_data[$i]['device_name']]) || count($machine_device_status[$machine_device_data[$i]['device_name']]) == 0) {
            //關機的機台
            $machine_device_data[$i]['now_status'] = 'S';
            continue;
        } else if (count($machine_device_status[$machine_device_data[$i]['device_name']][count($machine_device_status[$machine_device_data[$i]['device_name']]) - 1]) == 2) {
            //關機的機台
            $machine_device_data[$i]['now_status'] = 'S';
            continue;
        }

        //判斷機台是否異常，是的話狀態改為異常
        if ($machine_status_head_data[$i]['machine_detail'] != "") {
            $machine_detail = $machine_device_data[$i]['machine_detail'];
            foreach ($machine_abn_code as $machine_abn_code_key => $machine_abn_code_value) {
                if ($machine_detail['OPR'] == 1) {
                    $machine_device_data[$i]['now_status'] = 'R';//運轉
                } else {
                    $machine_device_data[$i]['now_status'] = 'Q';//閒置
                }
                if ($machine_abn_code_value['value'] == $machine_detail[$machine_abn_code_key]) {
                    if ($machine_abn_code_key == 'in_lube') {
                        if ($machine_detail['OPR'] == 1) {
                            $machine_device_data[$i]['now_status'] = 'H';
                        break;
                        }
                    } else {
                        $machine_device_data[$i]['now_status'] = 'H';
                    break;
                    }
                    //     $machine_device_data[$i]['now_status'] = 'H';
                    // break;
                }    
            }
        }

        //加入稼動率
        if (isset($device_activation_data[$machine_device_data[$i]['device_name']])) {
            $machine_device_data[$i]['activation'] = $device_activation_data[$machine_device_data[$i]['device_name']];
        }

        //計算產量
        if (isset($machine_work_code_runcard[$machine_device_data[$i]['device_name']])) {
            for ($j=0; $j < count($work_order_data); $j++) { 
                foreach ($machine_work_code_runcard[$machine_device_data[$i]['device_name']] as $machine_work_code => $machine_work_code_weight) {
                    if ($machine_work_code == $work_order_data[$j]['work_order$code']) {
                        if (!isset($machine_device_data[$i]['count'])) {
                            $machine_device_data[$i]['count'] = 0;
                        }
                        $machine_device_data[$i]['count'] += round($machine_work_code_weight/$work_order_data[$j]['commodity$standard_weight']);
                    }
                }
            }
        }

        //計算良率
        if (isset($machine_work_code_use_wire_weight[$machine_device_data[$i]['device_name']])) {
            $work_code_count = 0;
            $work_code_yield_rate = 0;
            for ($j=0; $j < count($work_order_data); $j++) { 
                foreach ($machine_work_code_use_wire_weight[$machine_device_data[$i]['device_name']] as $machine_work_code => $machine_work_code_use_weight) {
                    if ($machine_work_code == $work_order_data[$j]['work_order$code']) {
                        if ($machine_work_code_use_weight == 0) {
                            $yield_rate = 0;
                        } else {
                            $yield_rate = round($machine_work_code_runcard[$machine_device_data[$i]['device_name']][$machine_work_code] / $work_order_data[$j]['commodity$standard_weight'] * $work_order_data[$j]['commodity$material_weight'] / $machine_work_code_use_weight * 100, 2);
                        }
                        $work_code_count++;
                        $work_code_yield_rate += $yield_rate;
                    }
                }
            }
            if ($work_code_count != 0) {
                $machine_device_data[$i]['yield_rate'] = round($work_code_yield_rate / $work_code_count, 2);
            } else {
                $machine_device_data[$i]['yield_rate'] = 0;
            }
        }
    }

    $returnData['Response'] = 'ok';
    $returnData['page'] = 'machstatus';
    $returnData['QueryTableData'] = [];
    for ($i=0; $i < count($machine_device_data); $i++) { 
        array_push($returnData['QueryTableData'], array(
            'product_line' => '成四組',//產線
            'device_name' => $machine_device_data[$i]['device_name'],//機台名稱
            'model' => array_key_exists("model",$machine_device_data[$i]) ? $machine_device_data[$i]['model'] : "--",//機台型號
            'activation' => array_key_exists("activation",$machine_device_data[$i]) ? ($machine_device_data[$i]['activation']>0?$machine_device_data[$i]['activation']:0) : "--",//稼動率
            'count' => $machine_device_data[$i]['now_status'] != 'S' ? $machine_device_data[$i]['machine_detail']['cnt'] : "--",//產量
            // 'count' => array_key_exists("count",$machine_device_data[$i]) ? $machine_device_data[$i]['count'] : "--",//產量
            'wire_weight' => $machine_device_data[$i]['machine_detail'] != "" && $machine_device_data[$i]['now_status'] != 'S' ? (array_key_exists("wire_weight",$machine_device_data[$i]['machine_detail']) ? $machine_device_data[$i]['machine_detail']['wire_weight'] : "--" ) : "",//線材重量
            'speed' => array_key_exists("speed",$machine_device_data[$i]) ? $machine_device_data[$i]['speed'] : "--",//轉速
            'health' => array_key_exists("health",$machine_device_data[$i]) ? $machine_device_data[$i]['health'] : "--",//健康度
            'yield_rate' => array_key_exists("yield_rate",$machine_device_data[$i]) ? ($machine_device_data[$i]['yield_rate']>0?$machine_device_data[$i]['yield_rate']:0) : "--",//良率
            'status' => $machine_device_data[$i]['now_status'],//狀態
            'wire_stack_data' => $wire_stack_data
        ));
    }
    return $returnData;

    // return $machine_device_data;
}

function SelectMachineQuery($params)//查詢指定機台
{
    $device_name = $params->device_name;

    $process = array(
        '打頭' => 5,
        '輾牙' => 6,
        '熱處理' => 7
    );

    $this_process = $process[$params->process];

    if ($this_process == 5) {
        $returnData = get_heading_machine_data($this_process, $device_name);
    } else if ($this_process == 6) {
        $returnData = get_thd_machine_data($this_process, $device_name);
    }

    return $returnData;
}

function get_heading_machine_data($this_process, $device_name){
    $time = array();
    $time['01紀錄起始時間'] = [];
    array_push($time['01紀錄起始時間'],microtime(true));
    $now_time = strtotime(date("Y-m-d H:i:s"));
    // 紀錄時間區間
    if ($now_time > strtotime(date("Y-m-d 08:00:00"))) {
        $time_interval = array(
            'start' => date("Y-m-d 08:00:00"),
            'end' => date("Y-m-d H:i:s", strtotime(date('Y-m-d 08:00:00'))+86400)
        );
    } else {
        $time_interval = array(
            'start' => date("Y-m-d H:i:s", strtotime(date('Y-m-d 08:00:00'))-86400),
            'end' => date("Y-m-d 08:00:00")
        );
    }
    array_push($time['01紀錄起始時間'],microtime(true));

    $time['02查詢開關機'] = [];
    array_push($time['02查詢開關機'],microtime(true));
    //查詢machine_on_off_hist，機台開關機時間
    [$machine_on_off_hist_data, $machine_on_off_hist_SQL] = machine_on_off_hist($device_name, $time_interval);

    if (count($machine_on_off_hist_data) == 0) {
        return 'machstatus:machine_on_off_hist_data query erro';
    }
    array_push($time['02查詢開關機'],microtime(true));

    $time['03查詢機台狀態'] = [];
    array_push($time['03查詢機台狀態'],microtime(true));
    // 查詢machine_status，機台當前狀態
    [$machine_status_data, $machine_status_head_SQL] = machine_status_head($device_name);

    if (count($machine_status_data) == 0) {
        return 'machstatus:machine_status_data query erro';
    }
    array_push($time['03查詢機台狀態'],microtime(true));

    $time['04用該值來儲存資料'] = [];
    array_push($time['04用該值來儲存資料'],microtime(true));
    //用該值來儲存資料
    $machine_device_data = $machine_status_data;
    if (is_string($machine_device_data[0]['machine_detail'])) {
        $machine_device_data[0]['machine_detail'] = json_decode($machine_device_data[0]['machine_detail'], true);
    }
    array_push($time['04用該值來儲存資料'],microtime(true));

    $time['05查詢異常資料'] = [];
    array_push($time['05查詢異常資料'],microtime(true));
    //查詢machine_abn，機台異常資料
    $machine_abn_data = machine_abn();
    array_push($time['05查詢異常資料'],microtime(true));

    $time['06查詢機台基本資料'] = [];
    array_push($time['06查詢機台基本資料'],microtime(true));
    //查詢device_box，查詢機台基本資料
    [$device_box_data, $device_box_SQL]= device_box($device_name);
    
    if (count($device_box_data) == 0) {
        return 'machstatus:device_box_data query erro';
    }
    array_push($time['06查詢機台基本資料'],microtime(true));

    $time['07查詢機台燈號'] = [];
    array_push($time['07查詢機台燈號'],microtime(true));
    //查詢device_box，查詢機台基本資料
    if ($device_box_data[0]['model'] != '') {
        [$machine_status_list_data, $machine_status_list_SQL]= machine_status_list($device_box_data[0]['model']);
        if (is_string($machine_status_list_data[0]['light_list'])) {
            $machine_status_list_data[0]['light_list'] = json_decode($machine_status_list_data[0]['light_list'], true);
        }
    } else {
        $machine_status_list_data = [];
    }
    array_push($time['07查詢機台燈號'],microtime(true));

    $time['08取得該機台的燈號異常值'] = [];
    array_push($time['08取得該機台的燈號異常值'],microtime(true));
    //取得該機台的燈號異常值
    $machine_light_abn_data = machine_light_abn_data($machine_status_list_data[0]['light_list'], $machine_abn_data);
    array_push($time['08取得該機台的燈號異常值'],microtime(true));
    
    $time['09查詢單一機台當日資料與機台產量'] = [];
    array_push($time['09查詢單一機台當日資料與機台產量'],microtime(true));
    //查詢單一機台當日資料與機台產量
    [$Query_Device_Response, $device_out_put_data, $device_now_count] = Query_Device($time_interval['start'], date("Y-m-d H:i:s", $now_time), $device_name, $machine_on_off_hist_data, $machine_light_abn_data, $this_process);
    array_push($time['09查詢單一機台當日資料與機台產量'],microtime(true));

    $time['10確認機台狀態'] = [];
    array_push($time['10確認機台狀態'],microtime(true));
    //確認機台狀態
    $device_status = Get_device_status($machine_on_off_hist_data, $machine_device_data, $machine_light_abn_data, $this_process);
    array_push($time['10確認機台狀態'],microtime(true));

    //若有工單，則查詢工單、產品、線材資料 、檢測資料
    if ($machine_device_data[0]['work_code'] != "") {
        $time['11取得工單基本資料'] = [];
        array_push($time['11取得工單基本資料'],microtime(true));
        [$workorder_detail_data, $specification_data, $query_workorder_detail_SQL] = query_workorder_detail($device_name, $machine_device_data[0]['work_code'], $this_process);
        $process_name = array(5 => '打頭');
        array_push($time['11取得工單基本資料'],microtime(true));

        $time['12工單上下線資料'] = [];
        array_push($time['12工單上下線資料'],microtime(true));
        [$work_code_use_data, $work_code_use_SQL] = work_code_use($machine_device_data[0]['device_name'], $machine_device_data[0]['work_code'], $this_process);
        //取得工單開始時間
        $wrok_code_start_time = '';
        foreach ($work_code_use_data as $key => $value) {
            if ($value['status'] == 'S') {
                !empty($wrok_code_start_time) ? (strtotime($value['upload_at']) > strtotime($wrok_code_start_time) ? $wrok_code_start_time = $value['upload_at'] : '') : $wrok_code_start_time = $value['upload_at'];
            }
        }
        array_push($time['12工單上下線資料'],microtime(true));
        
        $time['13模具上線資料'] = [];
        array_push($time['13模具上線資料'],microtime(true));
        [$mould_series_no_use_data, $mould_series_no_use_SQL] = mould_series_no_use($machine_device_data[0]['work_code'], $wrok_code_start_time);
        array_push($time['13模具上線資料'],microtime(true));

        $time['14線材上線資料'] = [];
        array_push($time['14線材上線資料'],microtime(true));
        [$wire_scroll_no_use_data, $wire_scroll_no_use_SQL] = wire_scroll_no_use($machine_device_data[0]['work_code'], $wrok_code_start_time);
        array_push($time['14線材上線資料'],microtime(true));

        $time['15檢驗資料'] = [];
        array_push($time['15檢驗資料'],microtime(true));
        [$inspection_data, $inspection_SQL] = inspection($machine_device_data[0]['work_code'], $this_process, $wrok_code_start_time);
        array_push($time['15檢驗資料'],microtime(true));

        $time['16流程卡資料'] = [];
        array_push($time['16流程卡資料'],microtime(true));
        [$runcard_data, $runcard_SQL] = runcard($machine_device_data[0]['work_code'], $this_process, $wrok_code_start_time);
        array_push($time['16流程卡資料'],microtime(true));

        $time['17線材起始重量'] = [];
        array_push($time['17線材起始重量'],microtime(true));
        //線材起始重量
        $wire_start_weight;
        $wire_now_weight;
        $wire_now_scroll_no;
        $wire_consumption;
        if (count($wire_scroll_no_use_data) != 0) {
            if ($wire_scroll_no_use_data[count($wire_scroll_no_use_data) - 1]['status'] == 'S') {
                $wire_start_weight = $wire_scroll_no_use_data[count($wire_scroll_no_use_data) - 1]['weight'];
                $wire_now_weight = $machine_device_data[0]['machine_detail']['wire_weight'];
                $wire_now_scroll_no = $wire_scroll_no_use_data[count($wire_scroll_no_use_data) - 1]['scroll_no'];
                
                [$wire_scroll_no_use_data, $wire_scroll_no_use_SQL] = wire_scroll_no_use($machine_device_data[0]['work_code'], $wrok_code_start_time);
            }
        }
        array_push($time['17線材起始重量'],microtime(true));

        $time['18檢驗單支重'] = [];
        array_push($time['18檢驗單支重'],microtime(true));
        //檢驗單支重
        $inspection_data_length = count($inspection_data);
        $inspection_total = 0;
        $inspection_actual_weight = 0;
        for ($i=0; $i < $inspection_data_length; $i++) { 
            //加總每筆檢驗資料的單支重
            $inspection_total += floatval($inspection_data[$i]['inspection_detail']['act_wgt']);
        }
        if ($inspection_data_length != 0) {
            //平均單筆單支重=實際單支重
            $inspection_actual_weight = round($inspection_total / $inspection_data_length, 2);
        }
        array_push($time['18檢驗單支重'],microtime(true));
        
        $time['19儲存工單基本資料'] = [];
        array_push($time['19儲存工單基本資料'],microtime(true));
        //工單基本資料
        $work_order_detail_data = array(
            'workCode' => $machine_device_data[0]['work_code'],//工單
            'workOrgCode' => $workorder_detail_data[0]['work_org_code'],//原始工單編號
            'work_status' => count($work_code_use_data) == 0 ? '未加工' : ($work_code_use_data[count($work_code_use_data) - 1]['status'] == 'S' ? '加工中' : '完工'),//工單狀態
            'work_qty' => $workorder_detail_data[0]['work_qty'],//派工數量
            'device_count' => !empty($device_now_count) ? $device_now_count : '--',//計數器支數
            'productCode' => $workorder_detail_data[0]['commodity_code'],//料號
            'work_control_card' => $workorder_detail_data[0]['control_card'],//管制卡號
            'product_chinese_name' => $workorder_detail_data[0]['commodity_chinese_name'],//料名
            'wire_code' => $workorder_detail_data[0]['wire_code'],//線材品號
            'wire_chinese_name' => $workorder_detail_data[0]['wire_chinese_name'],//線材品名
            'wire_start_weight' => isset($wire_start_weight) ? $wire_start_weight : '--',//線材起始重量
            'wire_now_weight' => isset($wire_now_weight) ? $wire_now_weight : '--',//剩餘線材重量
            'wire_consumption' => isset($wire_consumption) ? $wire_consumption : '--',//線材使用量
            'standard_weight' => $workorder_detail_data[0]['standard_weight'],//標準單支重
            'standard_total_weight' => $workorder_detail_data[0]['work_qty'] != '-' ?  round(($workorder_detail_data[0]['standard_weight'] * $workorder_detail_data[0]['work_qty']) / 1000, 2) : '-',//標準生產總重量
            'material_weight' => $workorder_detail_data[0]['material_weight'],//標準單支原料使用重量
            'material_total_weight' => $workorder_detail_data[0]['work_qty'] != '-' ?  round(($workorder_detail_data[0]['material_weight'] * $workorder_detail_data[0]['work_qty']) / 1000, 2) : '-',//標準原料使用總重量
            'actual_weight' => $this_process == 5 ? ($inspection_actual_weight == 0 ? '--' : $inspection_actual_weight) : '--',//實際單支重
        );
        array_push($time['19儲存工單基本資料'],microtime(true));

        $time['20線材使用資訊'] = [];
        array_push($time['20線材使用資訊'],microtime(true));
        //線材使用資訊
        [$wire_use_information, $wire_total_weight, $wire_loss_rate, $wire_now_scroll_no_rack_wgt, $wire_stack_SQL] = wire_use_information($wire_scroll_no_use_data, $work_order_detail_data['material_total_weight'], isset($wire_now_scroll_no)?$wire_now_scroll_no:null);
        $wire_use_information_data = array(
            'wire_use_information' => $wire_use_information,
            'wire_total_weight' => $wire_total_weight,
            'wire_loss_rate' => $wire_loss_rate
        );
        $wire_now_weight = $wire_now_weight - $wire_now_scroll_no_rack_wgt;
        if ($wire_now_weight < 0) {
            $wire_now_weight = 0;
        }
        $wire_consumption = $wire_start_weight - $wire_now_weight;
        if ($wire_consumption < 0) {
            $wire_consumption = 0;
        }
        $work_order_detail_data['wire_now_weight'] = $wire_now_weight;
        $work_order_detail_data['wire_consumption'] = $wire_consumption;
        array_push($time['20線材使用資訊'],microtime(true));

        $time['21使用模具'] = [];
        array_push($time['21使用模具'],microtime(true));
        //使用模具
        [$mold_use_information, $mould_SQL,$mould_data] = mold_use_information($mould_series_no_use_data);
        $mold_use_information_data = array(
            'mold_use_information' => $mold_use_information
        );
        array_push($time['21使用模具'],microtime(true));

        
        $time['22每桶產出'] = [];
        array_push($time['22每桶產出'],microtime(true));
        //每桶產出
        $bucket_use_information = bucket_use_information($runcard_data);
        $bucket_use_information_data = array(
            'bucket_use_information' => $bucket_use_information,
        );
        array_push($time['22每桶產出'],microtime(true));

        $time['23檢驗數據'] = [];
        array_push($time['23檢驗數據'],microtime(true));
        //檢驗數據
        $inspection_use_information = inspection_use_information($specification_data, $inspection_data, $work_order_detail_data['standard_weight']);
        $inspection_use_information_data = array(
            'inspection_use_information' => $inspection_use_information
        );
        array_push($time['23檢驗數據'],microtime(true));

        $time['24總生產時間'] = [];
        array_push($time['24總生產時間'],microtime(true));
        //總生產時間
        [$totalProduceTime, $total_work_time] = totalProduceTime($device_name, $work_code_use_data, $process_name);
        $totalProduceTime_data = array(
            'totalProduceTime' => $totalProduceTime,
            'total_work_time' => $total_work_time
        );
        array_push($time['24總生產時間'],microtime(true));
    }

    $time['25機台運轉時間'] = [];
    array_push($time['25機台運轉時間'],microtime(true));
    $device_run_time_second = 0;
    foreach ($Query_Device_Response[0]['machine_detail']['R']['datail'] as $key => $value) {
        $device_run_time_second += strtotime($value['timestamp'][1]) - strtotime($value['timestamp'][0]);
    }
    $device_run_time = change_time($device_run_time_second, 'h:m');
    array_push($time['25機台運轉時間'],microtime(true));

    $time['26堆疊圖與運轉日誌'] = [];
    array_push($time['26堆疊圖與運轉日誌'],microtime(true));
    $stack_bar_data = array(
        $device_name => array()
    );
    $operatelog_data = [];
    foreach ($Query_Device_Response[0]['machine_detail'] as $status => $value) {
        foreach ($value['datail'] as $datail) {
            $startTime = date("Y-m-d H:i:s",strtotime($datail['timestamp'][0]));
            $endTime = date("Y-m-d H:i:s",strtotime($datail['timestamp'][1]));
            $durationTime = TimeSubtraction($startTime, $endTime, 'hour');
            array_push($operatelog_data, array(
                'device_name' => $device_name,
                'place_item' => '二廠',
                'group_item' => '成四組',
                'class_item' => '日班',
                'status' => $status == 'S' ? '關機' : ($status == 'H' ? '警報' : ($status == 'R' ? '生產' : ($status == 'Q' ? '待機' : ''))),
                'alarmCode' => isset($datail['machine_abn_id'])?implode("\n",$datail['machine_abn_id']):'',
                'alarmDetail' => isset($datail['machine_abn_description'])?implode("\n",$datail['machine_abn_description']):'',
                'startTime' =>  $startTime,
                'endTime' => $endTime,
                'durationTime' => $durationTime[0]
            ));
            array_push($stack_bar_data[$device_name], array(
                'status' => $status == 'S' ? '關機' : ($status == 'H' ? '警報' : ($status == 'R' ? '生產' : ($status == 'Q' ? '待機' : ''))),
                'alarmDetail' => isset($datail['machine_abn_description'])?implode("\n",$datail['machine_abn_description']):'',
                'startTime' =>  $startTime,
                'endTime' => $endTime,
                'duration_number' => $durationTime[2]
            ));
        }
        usort($operatelog_data, 'sort_start_time');
        usort($stack_bar_data[$device_name], 'sort_start_time');
    }
    if (count($stack_bar_data[$device_name]) > 0) {
        if ($stack_bar_data[$device_name][count($stack_bar_data[$device_name])-1]['status'] == '關機' && $stack_bar_data[$device_name][count($stack_bar_data[$device_name])-1]['duration_number'] < 120) {
            array_pop($stack_bar_data[$device_name]);
            array_pop($operatelog_data);
        }
    }
    array_push($time['26堆疊圖與運轉日誌'],microtime(true));

    $time['27機台燈號'] = [];
    array_push($time['27機台燈號'],microtime(true));
    if (!empty($machine_status_list_data[0]['light_list'])) {
        [$machine_light, $machine_item] = machine_light($machine_device_data[0]['machine_detail'], $machine_status_list_data[0]['light_list'], $machine_abn_data, $device_status);
    } else {
        $machine_light = [];
        $machine_item = [];
    }
    array_push($time['27機台燈號'],microtime(true));

    $time['28查詢機台圖片檔名'] = [];
    array_push($time['28查詢機台圖片檔名'],microtime(true));
    [$machine_model_image_data, $machine_model_image_SQL] = machine_model_image($device_box_data[0]['model']);
    array_push($time['28查詢機台圖片檔名'],microtime(true));

    $time['29儲存機台基本資料'] = [];
    array_push($time['29儲存機台基本資料'],microtime(true));
    $device_detail_data = array(
        'product_line' => '成四組',//產線
        'device_name' => $device_name,//機號
        'device_status' => $device_status,//狀態
        'device_model' => $device_box_data[0]['model'],//型號
        'device_run_time' => $device_run_time,//運轉時間
        'device_activation' => $Query_Device_Response[0]['machine_detail']['R']['rate'],//開機稼動率
        'device_cumulative_production' => isset($device_out_put_data) ? $device_out_put_data : '--',//累計產量
        'device_capacity' => round($device_box_data[0]['capacity_hr']/60, 0),//標準RPM
        'device_image' => isset($machine_model_image_data[0]['img_name'])?explode('.',$machine_model_image_data[0]['img_name'])[0]:''//機台圖片
    );
    array_push($time['29儲存機台基本資料'],microtime(true));

    $time['30儲存機台燈號相關資料'] = [];
    array_push($time['30儲存機台燈號相關資料'],microtime(true));
    $machine_light_information = array(
        'machine_item' => isset($machine_item) ? $machine_item : [],//機型燈號
        'machine_light' => isset($machine_light) ? $machine_light : [],//機台燈號值
    );
    array_push($time['30儲存機台燈號相關資料'],microtime(true));

    $time_total=0;
    $time_out_put = array();
    foreach ($time as $key => $value) {
        $this_time = round($value[1]-$value[0],5);
        array_push($time[$key],$this_time); 
        $time_out_put[$key] = $this_time;
        $time_total += $this_time;
    }
    $time_log = array(
        'machine_on_off_hist_SQL' => isset($machine_on_off_hist_SQL) ? $machine_on_off_hist_SQL : '',
        'machine_status_head_SQL' => isset($machine_status_head_SQL) ? $machine_status_head_SQL : '',
        'device_box_SQL' => isset($device_box_SQL) ? $device_box_SQL : '',
        'query_workorder_detail_SQL' => isset($query_workorder_detail_SQL) ? $query_workorder_detail_SQL : '',
        'mould_series_no_use_SQL' => isset($mould_series_no_use_SQL) ? $mould_series_no_use_SQL : '',
        'thread_series_no_use_SQL' => isset($thread_series_no_use_SQL) ? $thread_series_no_use_SQL : '',
        'wire_scroll_no_use_SQL' => isset($wire_scroll_no_use_SQL) ? $wire_scroll_no_use_SQL : '',
        'inspection_SQL' => isset($inspection_SQL) ? $inspection_SQL : '',
        'workhour_SQL' => isset($workhour_SQL) ? $workhour_SQL : '',
        'runcard_SQL' => isset($runcard_SQL) ? $runcard_SQL : '',
        'wire_stack_SQL' => isset($wire_stack_SQL) ? $wire_stack_SQL : '',
        'mould_SQL' => isset($mould_SQL) ? $mould_SQL : '',
        'work_code_use_SQL' => isset($work_code_use_SQL) ? $work_code_use_SQL : '',
        'time' => isset($time) ? $time : '',
        'time_total' => isset($time_total) ? $time_total : '',
        'time_out_put' => isset($time_out_put) ? $time_out_put : ''
    );

    $returnData['Response'] = 'ok';
    $returnData['page'] = 'machstatus';
    $returnData['QueryTableData'] = [];
    array_push($returnData['QueryTableData'], array(
        'work_order_detail' => $machine_device_data[0]['work_code'] != '' ? $work_order_detail_data : [],
        'device_detail' => $device_detail_data,
        'stack_bar' => $stack_bar_data,
        'wire_use_information' => isset($wire_use_information_data) ? $wire_use_information_data : array(
            'wire_use_information' => [],
            'wire_total_weight' => '--',
            'wire_loss_rate' => '--'
        ),
        'mold_use_information' => isset($mold_use_information_data) ? $mold_use_information_data : array(
            'mold_use_information' => []
        ),
        'bucket_use_information' => isset($bucket_use_information_data) ? $bucket_use_information_data : array(
            'bucket_use_information' => []
        ),
        'inspection_use_information' => isset($inspection_use_information_data) ? $inspection_use_information_data : array(
            'inspection_use_information' => []
        ),
        'totalProduceTime' => isset($totalProduceTime_data) ? $totalProduceTime_data : array(
            'totalProduceTime' => [],
            'total_work_time' => '--'
        ),
        'machine_light_information' => isset($machine_light_information) ? $machine_light_information : array(
            'machine_item' => [],
            'machine_light' => []
        ),
        'operatelog' => isset($operatelog_data) ? $operatelog_data : [],
        'time' => $time_log
    ));

    return $returnData;
}

function get_thd_machine_data($this_process, $device_name){
    $time = array();
    $time['01紀錄起始時間'] = [];
    array_push($time['01紀錄起始時間'],microtime(true));
    $now_time = strtotime(date("Y-m-d H:i:s"));
    // 紀錄時間區間
    if ($now_time > strtotime(date("Y-m-d 08:00:00"))) {
        $time_interval = array(
            'start' => date("Y-m-d 08:00:00"),
            'end' => date("Y-m-d H:i:s", strtotime(date('Y-m-d 08:00:00'))+86400)
        );
    } else {
        $time_interval = array(
            'start' => date("Y-m-d H:i:s", strtotime(date('Y-m-d 08:00:00'))-86400),
            'end' => date("Y-m-d 08:00:00")
        );
    }
    array_push($time['01紀錄起始時間'],microtime(true));

    $time['02查詢開關機'] = [];
    array_push($time['02查詢開關機'],microtime(true));
    //查詢machine_on_off_hist，機台開關機時間
    [$machine_on_off_hist_data, $machine_on_off_hist_SQL] = machine_on_off_hist($device_name, $time_interval);

    if (count($machine_on_off_hist_data) == 0) {
        return 'machstatus:machine_on_off_hist_data query erro';
    }
    array_push($time['02查詢開關機'],microtime(true));

    $time['03查詢機台狀態'] = [];
    array_push($time['03查詢機台狀態'],microtime(true));
    // 查詢machine_status，機台當前狀態
    [$machine_status_data, $machine_status_thd_SQL] = machine_status_thd($device_name);

    if (count($machine_status_data) == 0) {
        return 'machstatus:machine_status_data query erro';
    }
    array_push($time['03查詢機台狀態'],microtime(true));

    $time['04用該值來儲存資料'] = [];
    array_push($time['04用該值來儲存資料'],microtime(true));
    //用該值來儲存資料
    $machine_device_data = $machine_status_data;
    if (is_string($machine_device_data[0]['machine_detail'])) {
        $machine_device_data[0]['machine_detail'] = json_decode($machine_device_data[0]['machine_detail'], true);
    }
    array_push($time['04用該值來儲存資料'],microtime(true));

    $time['05查詢異常資料'] = [];
    array_push($time['05查詢異常資料'],microtime(true));
    //查詢machine_abn，機台異常資料
    $machine_abn_data = machine_abn();
    array_push($time['05查詢異常資料'],microtime(true));

    $time['06查詢機台基本資料'] = [];
    array_push($time['06查詢機台基本資料'],microtime(true));
    //查詢device_box，查詢機台基本資料
    [$device_box_data, $device_box_SQL]= device_box($device_name);
    
    if (count($device_box_data) == 0) {
        return 'machstatus:device_box_data query erro';
    }
    array_push($time['06查詢機台基本資料'],microtime(true));
    
    $time['07查詢機台燈號'] = [];
    array_push($time['07查詢機台燈號'],microtime(true));
    //查詢device_box，查詢機台基本資料
    if ($device_box_data[0]['model'] != '') {
        [$machine_status_list_data, $machine_status_list_SQL]= machine_status_list($device_box_data[0]['model']);
        if (is_string($machine_status_list_data[0]['light_list'])) {
            $machine_status_list_data[0]['light_list'] = json_decode($machine_status_list_data[0]['light_list'], true);
        }
    } else {
        $machine_status_list_data = [];
    }
    array_push($time['07查詢機台燈號'],microtime(true));

    $time['08取得該機台的燈號異常值'] = [];
    array_push($time['08取得該機台的燈號異常值'],microtime(true));
    //取得該機台的燈號異常值
    $machine_light_abn_data = machine_light_abn_data($machine_status_list_data[0]['light_list'], $machine_abn_data);
    array_push($time['08取得該機台的燈號異常值'],microtime(true));

    $time['09查詢單一機台當日資料與機台產量'] = [];
    array_push($time['09查詢單一機台當日資料與機台產量'],microtime(true));
    //查詢單一機台當日資料與機台產量
    [$Query_Device_Response, $device_out_put_data, $device_count] = Query_Device($time_interval['start'], date("Y-m-d H:i:s", $now_time), $device_name, $machine_on_off_hist_data, $machine_light_abn_data, $this_process);
    array_push($time['09查詢單一機台當日資料與機台產量'],microtime(true));

    $time['10確認機台狀態'] = [];
    array_push($time['10確認機台狀態'],microtime(true));
    //確認機台狀態
    $device_status = Get_device_status($machine_on_off_hist_data, $machine_device_data, $machine_light_abn_data, $this_process);
    array_push($time['10確認機台狀態'],microtime(true));

    //若有工單，則查詢工單、產品、線材資料 、檢測資料
    if ($machine_device_data[0]['work_code'] != "") {
        $time['11取得工單基本資料'] = [];
        array_push($time['11取得工單基本資料'],microtime(true));
        [$workorder_detail_data, $specification_data, $query_workorder_detail_SQL] = query_workorder_detail($device_name, $machine_device_data[0]['work_code'], $this_process);
        $process_name = array(6 => '輾牙');
        array_push($time['11取得工單基本資料'],microtime(true));

        $time['12工單上下線資料'] = [];
        array_push($time['12工單上下線資料'],microtime(true));
        [$work_code_use_data, $work_code_use_SQL] = work_code_use($machine_device_data[0]['device_name'], $machine_device_data[0]['work_code'], $this_process);
        //取得工單開始時間
        $wrok_code_start_time = '';
        foreach ($work_code_use_data as $key => $value) {
            if ($value['status'] == 'S') {
                !empty($wrok_code_start_time) ? (strtotime($value['upload_at']) > strtotime($wrok_code_start_time) ? $wrok_code_start_time = $value['upload_at'] : '') : $wrok_code_start_time = $value['upload_at'];
            }
        }
        array_push($time['12工單上下線資料'],microtime(true));

        $time['13檢驗資料'] = [];
        array_push($time['13檢驗資料'],microtime(true));
        [$inspection_data, $inspection_SQL] = inspection($machine_device_data[0]['work_code'], $this_process, $wrok_code_start_time);
        array_push($time['13檢驗資料'],microtime(true));

        $time['14牙板上線資料'] = [];
        array_push($time['14牙板上線資料'],microtime(true));
        [$thread_series_no_use_data, $thread_series_no_use_SQL] = thread_series_no_use($machine_device_data[0]['work_code'], $wrok_code_start_time);
        array_push($time['14牙板上線資料'],microtime(true));

        $time['15流程卡資料'] = [];
        array_push($time['15流程卡資料'],microtime(true));
        [$runcard_data, $runcard_SQL] = runcard($machine_device_data[0]['work_code'], $this_process, $wrok_code_start_time);
        array_push($time['15流程卡資料'],microtime(true));

        $time['16工時資料'] = [];
        array_push($time['16工時資料'],microtime(true));
        [$workhour_data, $workhour_SQL] = workhour($machine_device_data[0]['work_code'], $this_process, $wrok_code_start_time);
        array_push($time['16工時資料'],microtime(true));
        
        $time['17輾牙機台目前支數'] = [];
        array_push($time['17輾牙機台目前支數'],microtime(true));
        $device_now_count = get_start_count($device_name, $wrok_code_start_time, $device_count);
        array_push($time['17輾牙機台目前支數'],microtime(true));

        $time['18儲存工單基本資料'] = [];
        array_push($time['18儲存工單基本資料'],microtime(true));
        //工單基本資料
        $work_order_detail_data = array(
            'workCode' => $machine_device_data[0]['work_code'],//工單
            'workOrgCode' => $workorder_detail_data[0]['work_org_code'],//原始工單編號
            'work_status' => count($workhour_data) == 0 ? '未加工' : ($workhour_data[0]['status'] == 'S' ? '加工中' : '完工'),//工單狀態
            'work_qty' => $workorder_detail_data[0]['work_qty'],//派工數量
            'device_count' => !empty($device_now_count) ? $device_now_count : '--',//計數器支數
            'productCode' => $workorder_detail_data[0]['commodity_code'],//料號
            'work_control_card' => $workorder_detail_data[0]['control_card'],//管制卡號
            'product_chinese_name' => $workorder_detail_data[0]['commodity_chinese_name'],//料名
            'wire_code' => $workorder_detail_data[0]['wire_code'],//線材品號
            'wire_chinese_name' => $workorder_detail_data[0]['wire_chinese_name'],//線材品名
            'wire_start_weight' => isset($wire_start_weight) ? $wire_start_weight : '--',//線材起始重量
            'wire_now_weight' => isset($wire_now_weight) ? $wire_now_weight : '--',//剩餘線材重量
            'wire_consumption' => isset($wire_consumption) ? $wire_consumption : '--',//線材使用量
            'standard_weight' => $workorder_detail_data[0]['standard_weight'],//標準單支重
            'standard_total_weight' => $workorder_detail_data[0]['work_qty'] != '-' ? round(($workorder_detail_data[0]['standard_weight'] * $workorder_detail_data[0]['work_qty']) / 1000, 2) : '-',//標準生產總重量
            'material_weight' => $workorder_detail_data[0]['material_weight'],//標準單支原料使用重量
            'material_total_weight' => $workorder_detail_data[0]['work_qty'] != '-' ?  round(($workorder_detail_data[0]['material_weight'] * $workorder_detail_data[0]['work_qty']) / 1000, 2) : '-',//標準原料使用總重量
            'actual_weight' => $this_process == 5 ? ($inspection_actual_weight == 0 ? '--' : $inspection_actual_weight) : '--',//實際單支重
        );
        array_push($time['18儲存工單基本資料'],microtime(true));

        $time['19使用牙板'] = [];
        array_push($time['19使用牙板'],microtime(true));
        //使用模具
        [$thread_use_information, $mould_SQL,$mould_data] = thread_use_information($thread_series_no_use_data);
        $thread_use_information_data = array(
            'thread_use_information' => $thread_use_information
        );
        array_push($time['19使用牙板'],microtime(true));

        $time['20每桶產出'] = [];
        array_push($time['20每桶產出'],microtime(true));
        //每桶產出
        $bucket_use_information = bucket_use_information($runcard_data);
        $bucket_use_information_data = array(
            'bucket_use_information' => $bucket_use_information,
        );
        array_push($time['20每桶產出'],microtime(true));

        $time['21檢驗數據'] = [];
        array_push($time['21檢驗數據'],microtime(true));
        //檢驗數據
        $inspection_use_information = inspection_use_information($specification_data, $inspection_data, $work_order_detail_data['standard_weight']);
        $inspection_use_information_data = array(
            'inspection_use_information' => $inspection_use_information
        );
        array_push($time['21檢驗數據'],microtime(true));

        $time['22總生產時間'] = [];
        array_push($time['22總生產時間'],microtime(true));
        //總生產時間
        [$totalProduceTime, $total_work_time] = totalProduceTime($device_name, $work_code_use_data, $process_name);
        $totalProduceTime_data = array(
            'totalProduceTime' => $totalProduceTime,
            'total_work_time' => $total_work_time
        );
        array_push($time['22總生產時間'],microtime(true));
    }

    $time['23機台運轉時間'] = [];
    array_push($time['23機台運轉時間'],microtime(true));
    $device_run_time_second = 0;
    foreach ($Query_Device_Response[0]['machine_detail']['R']['datail'] as $key => $value) {
        $device_run_time_second += strtotime($value['timestamp'][1]) - strtotime($value['timestamp'][0]);
    }
    $device_run_time = change_time($device_run_time_second, 'h:m');
    array_push($time['23機台運轉時間'],microtime(true));

    $time['24堆疊圖與運轉日誌'] = [];
    array_push($time['24堆疊圖與運轉日誌'],microtime(true));
    $stack_bar_data = array(
        $device_name => array()
    );
    $operatelog_data = [];
    foreach ($Query_Device_Response[0]['machine_detail'] as $status => $value) {
        foreach ($value['datail'] as $datail) {
            $startTime = date("Y-m-d H:i:s",strtotime($datail['timestamp'][0]));
            $endTime = date("Y-m-d H:i:s",strtotime($datail['timestamp'][1]));
            $durationTime = TimeSubtraction($startTime, $endTime, 'hour');
            array_push($operatelog_data, array(
                'device_name' => $device_name,
                'place_item' => '二廠',
                'group_item' => '成四組',
                'class_item' => '日班',
                'status' => $status == 'S' ? '關機' : ($status == 'H' ? '警報' : ($status == 'R' ? '生產' : ($status == 'Q' ? '待機' : ''))),
                'alarmCode' => isset($datail['machine_abn_id'])?implode("\n",$datail['machine_abn_id']):'',
                'alarmDetail' => isset($datail['machine_abn_description'])?implode("\n",$datail['machine_abn_description']):'',
                'startTime' =>  $startTime,
                'endTime' => $endTime,
                'durationTime' => $durationTime[0]
            ));
            array_push($stack_bar_data[$device_name], array(
                'status' => $status == 'S' ? '關機' : ($status == 'H' ? '警報' : ($status == 'R' ? '生產' : ($status == 'Q' ? '待機' : ''))),
                'alarmDetail' => isset($datail['machine_abn_description'])?implode("\n",$datail['machine_abn_description']):'',
                'startTime' =>  $startTime,
                'endTime' => $endTime,
                'duration_number' => $durationTime[2]
            ));
        }
        usort($operatelog_data, 'sort_start_time');
        usort($stack_bar_data[$device_name], 'sort_start_time');
    }
    if (count($stack_bar_data[$device_name]) > 0) {
        if ($stack_bar_data[$device_name][count($stack_bar_data[$device_name])-1]['status'] == '關機' && $stack_bar_data[$device_name][count($stack_bar_data[$device_name])-1]['duration_number'] < 120) {
            array_pop($stack_bar_data[$device_name]);
            array_pop($operatelog_data);
        }
    }
    array_push($time['24堆疊圖與運轉日誌'],microtime(true));

    $time['25機台燈號'] = [];
    array_push($time['25機台燈號'],microtime(true));
    if (!empty($machine_status_list_data[0]['light_list'])) {
        [$machine_light, $machine_item] = machine_light($machine_device_data[0]['machine_detail'], $machine_status_list_data[0]['light_list'], $machine_abn_data, $device_status);
    } else {
        $machine_light = [];
        $machine_item = [];
    }
    array_push($time['25機台燈號'],microtime(true));

    $time['26查詢機台圖片檔名'] = [];
    array_push($time['26查詢機台圖片檔名'],microtime(true));
    [$machine_model_image_data, $machine_model_image_SQL] = machine_model_image($device_box_data[0]['model']);
    array_push($time['26查詢機台圖片檔名'],microtime(true));

    $time['27儲存機台基本資料'] = [];
    array_push($time['27儲存機台基本資料'],microtime(true));
    $device_detail_data = array(
        'product_line' => '成四組',//產線
        'device_name' => $device_name,//機號
        'device_status' => $device_status,//狀態
        'device_model' => $device_box_data[0]['model'],//型號
        'device_run_time' => $device_run_time,//運轉時間
        'device_activation' => $Query_Device_Response[0]['machine_detail']['R']['rate'],//開機稼動率
        'device_cumulative_production' => isset($device_out_put_data) ? $device_out_put_data : '--',//累計產量
        'device_capacity' => round($device_box_data[0]['capacity_hr']/60, 0),//標準RPM
        'device_image' => isset($machine_model_image_data[0]['img_name'])?explode('.',$machine_model_image_data[0]['img_name'])[0]:''//機台圖片
    );
    array_push($time['27儲存機台基本資料'],microtime(true));

    $time['28儲存機台燈號相關資料'] = [];
    array_push($time['28儲存機台燈號相關資料'],microtime(true));
    $machine_light_information = array(
        'machine_item' => isset($machine_item) ? $machine_item : [],//機型燈號
        'machine_light' => isset($machine_light) ? $machine_light : [],//機台燈號值
    );
    array_push($time['28儲存機台燈號相關資料'],microtime(true));

    $time_total=0;
    $time_out_put = array();
    foreach ($time as $key => $value) {
        $this_time = round($value[1]-$value[0],5);
        array_push($time[$key],$this_time); 
        $time_out_put[$key] = $this_time;
        $time_total += $this_time;
    }
    $time_log = array(
        'machine_on_off_hist_SQL' => isset($machine_on_off_hist_SQL) ? $machine_on_off_hist_SQL : '',
        'machine_status_head_SQL' => isset($machine_status_head_SQL) ? $machine_status_head_SQL : '',
        'device_box_SQL' => isset($device_box_SQL) ? $device_box_SQL : '',
        'query_workorder_detail_SQL' => isset($query_workorder_detail_SQL) ? $query_workorder_detail_SQL : '',
        'mould_series_no_use_SQL' => isset($mould_series_no_use_SQL) ? $mould_series_no_use_SQL : '',
        'thread_series_no_use_SQL' => isset($thread_series_no_use_SQL) ? $thread_series_no_use_SQL : '',
        'wire_scroll_no_use_SQL' => isset($wire_scroll_no_use_SQL) ? $wire_scroll_no_use_SQL : '',
        'inspection_SQL' => isset($inspection_SQL) ? $inspection_SQL : '',
        'workhour_SQL' => isset($workhour_SQL) ? $workhour_SQL : '',
        'runcard_SQL' => isset($runcard_SQL) ? $runcard_SQL : '',
        'wire_stack_SQL' => isset($wire_stack_SQL) ? $wire_stack_SQL : '',
        'mould_SQL' => isset($mould_SQL) ? $mould_SQL : '',
        'work_code_use_SQL' => isset($work_code_use_SQL) ? $work_code_use_SQL : '',
        'time' => isset($time) ? $time : '',
        'time_total' => isset($time_total) ? $time_total : '',
        'time_out_put' => isset($time_out_put) ? $time_out_put : ''
    );

    $returnData['Response'] = 'ok';
    $returnData['page'] = 'machstatus';
    $returnData['QueryTableData'] = [];

    array_push($returnData['QueryTableData'], array(
        'work_order_detail' => $machine_device_data[0]['work_code'] != '' ? $work_order_detail_data : [],
        'device_detail' => $device_detail_data,
        'stack_bar' => $stack_bar_data,
        'thread_use_information' => isset($thread_use_information_data) ? $thread_use_information_data : array(
            'thread_use_information' => []
        ),
        'bucket_use_information' => isset($bucket_use_information_data) ? $bucket_use_information_data : array(
            'bucket_use_information' => []
        ),
        'inspection_use_information' => isset($inspection_use_information_data) ? $inspection_use_information_data : array(
            'inspection_use_information' => []
        ),
        'totalProduceTime' => isset($totalProduceTime_data) ? $totalProduceTime_data : array(
            'totalProduceTime' => [],
            'total_work_time' => '--'
        ),
        'machine_light_information' => isset($machine_light_information) ? $machine_light_information : array(
            'machine_item' => [],
            'machine_light' => []
        ),
        'operatelog' => isset($operatelog_data) ? $operatelog_data : [],
        'time' => $time_log
    ));
    return $returnData;
}

//查詢machine_on_off_hist，機台開關機時間
function machine_on_off_hist($device_name, $time_interval){
    $intervaltime = array(
        'upload_at' => array(array($time_interval['start'], $time_interval['end']))
    );
    $whereAttr = new stdClass();
    $whereAttr->device_name = [strtolower($device_name)];
    $symbols = new stdClass();
    $symbols->device_name = ['equal'];
    $data = array(
        'condition_1' => array(
            'table' => 'machine_on_off_hist',
            'intervaltime' => $intervaltime,
            'limit' => ['ALL'],
            'orderby' => ['asc','upload_at'],
            'symbols' => $symbols,
            'where' => $whereAttr,
        )
    );
    $machine_on_off_hist = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    if ($machine_on_off_hist['Response'] !== 'ok') {
        return [[],[],''];
        // return $machine_on_off_hist;
    } else if (count($machine_on_off_hist['QueryTableData']) == 0) {
        $data = array(
            'condition_1' => array(
                'table' => 'machine_on_off_hist',
                'limit' => [0,1],
                'orderby' => ['desc','upload_at'],
                'symbols' => $symbols,
                'where' => $whereAttr,
            )
        );
        $machine_on_off_hist_second = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
        if ($machine_on_off_hist_second['Response'] !== 'ok') {
            return [[],[],''];
            // return $machine_on_off_hist_second;
        } else if (count($machine_on_off_hist_second['QueryTableData']) == 0) {
            array_push($machine_on_off_hist['QueryTableData'], array(
                'comp_id' => "OFCO",
                'device_name' => strtolower($device_name),
                'site_id' => 1,
                'status' => "E",
                'upload_at' => $time_interval['start'],
            ));
        } else {
            if (strtotime($machine_on_off_hist_second['QueryTableData'][0]['upload_at']) < strtotime($time_interval['start'])) {
                $machine_on_off_hist_second['QueryTableData'][0]['upload_at'] = $time_interval['start'];
            }
            array_push($machine_on_off_hist['QueryTableData'], $machine_on_off_hist_second['QueryTableData'][0]);
        }
    }
    return [$machine_on_off_hist['QueryTableData'],[$machine_on_off_hist['SqlSyntax'],'time:'.$machine_on_off_hist['OperationTime']]];
}

// 查詢machine_status，機台當前狀態
// 打頭
function machine_status_head($device_name){
    $whereAttr = new stdClass();
    $whereAttr->device_name = [$device_name];
    $symbols = new stdClass();
    $symbols->device_name = ['equal'];
    $data = array(
        'condition_1' => array(
            'fields' => ['device_name', 'work_code', 'machine_detail'],
            'table' => 'machine_status_head',
            'limit' => [0,1],
            'symbols' => $symbols,
            'where' => $whereAttr,
        )
    );
    $machine_status_head = CommonSqlSyntax_Query($data, "MySQL");
    if ($machine_status_head['Response'] !== 'ok') {
        return [[],[]];
    } else if (count($machine_status_head['QueryTableData']) == 0) {
        return [[],[]];
    }
    return [$machine_status_head['QueryTableData'], [$machine_status_head['SqlSyntax'],'time:'.$machine_status_head['OperationTime']]];
}
//輾牙
function machine_status_thd($device_name){
    $whereAttr = new stdClass();
    $whereAttr->device_name = [$device_name];
    $symbols = new stdClass();
    $symbols->device_name = ['equal'];
    $data = array(
        'condition_1' => array(
            'fields' => ['device_name', 'work_code', 'machine_detail'],
            'table' => 'machine_status_thd',
            'limit' => [0,1],
            'symbols' => $symbols,
            'where' => $whereAttr,
        )
    );
    $machine_status_thd = CommonSqlSyntax_Query($data, "MySQL");
    if ($machine_status_thd['Response'] !== 'ok') {
        return [[],[]];
    } else if (count($machine_status_thd['QueryTableData']) == 0) {
        return [[],[]];
    }
    return [$machine_status_thd['QueryTableData'], [$machine_status_thd['SqlSyntax'],'time:'.$machine_status_thd['OperationTime']]];
}

//查詢machine_abn，機台異常資料
function machine_abn(){
    $machine_abn = CommonTableQuery('MySQL', 'machine_abn');
    if ($machine_abn['Response'] !== 'ok') {
        return [];
    } else if (count($machine_abn['QueryTableData']) == 0) {
        return [];
    }
    $machine_abn_data = $machine_abn['QueryTableData'];
    $machine_abn_code = [];
    for ($i=0; $i < count($machine_abn_data); $i++) { 
        $machine_abn_code[$machine_abn_data[$i]['name']] = array(
            'description' => $machine_abn_data[$i]['description'],
            'err_code' => $machine_abn_data[$i]['err_code'],
            'value' => $machine_abn_data[$i]['value']
        );
    }
    return $machine_abn_code;
}

function Query_Device($startTime, $endTime, $device_name, $machine_on_off_hist_data, $machine_light_abn_data, $process) {
    $now_time = $endTime;
    $previous_time = $startTime;
    $totalTime = strtotime($now_time) - strtotime($previous_time);

    //處理各機台
    $machine_status = [];
    //查詢單一機台當日資料
    $device_data = Query_Device_Data($device_name, $previous_time, $now_time);

    //將$device_data內的JSON字串轉為Object
    foreach ($device_data as $key => $value) {
        if (is_string($value['machine_detail'])) {
            $machine_detail = json_decode($value['machine_detail'], true);
            $device_data[$key]['machine_detail'] = $machine_detail;
        }
    }

    //整理取得該機台當日支數資料
    $device_out_put_data = Get_Device_Out_Put($device_data);
    //取得機台目前支數
    $device_now_count = Get_Device_Now_Count($device_data);

    //整理取得該機台當日時間區間資料
    $device_detail_data = Get_Device_Detail_Time($device_data, $machine_light_abn_data, $previous_time, $process);

    //若當日有資料才做
    if (!empty($device_detail_data)) {

        //紀錄停機時間
        $machine_status_S = Device_Stop_Time($device_name, $machine_on_off_hist_data, $previous_time, $now_time);
        //加總停機時間
        [$machine_status_S_time_rate, $machine_status_S_time_array] = Device_All_Time($machine_status_S, $totalTime);

        //整理出停機以外的時間資料
        $device_detail_time_data = Device_Detail_Time($device_name, $device_detail_data, $machine_status_S, $previous_time, $now_time);

        //整理出異常、運轉、待機時間
        [$machine_status_H, $machine_status_R, $machine_status_Q] = Device_Status_Time($device_name, $device_detail_time_data, $process, $machine_light_abn_data, $machine_status_S, $previous_time, $now_time);
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

    if (!empty($machine_status)) {
        $push_data = [];
        foreach ($machine_status as $device_name => $value) {
            array_push($push_data, array(
                'device_name' => $device_name,
                'machine_detail' => $value,
            ));
        }
    } else {
        return [null, $device_out_put_data, $device_now_count];
    }
    return [$push_data, $device_out_put_data, $device_now_count];
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

//整理取得該機台當日支數資料
function Get_Device_Out_Put($device_data){
    $old_count = 0;
    $start_count = 0;
    $out_put_count = [];//產出數量
    foreach ($device_data as $key => $value) {
        $machine_detail = $value['machine_detail'];
        $new_count = 0;
        $new_count = $machine_detail['cnt'];
        if ($key == 0) {
            $start_count = $new_count;
            $old_count = $new_count;
        } else if ($key == count($device_data) - 1) {
            if ($new_count >= $old_count) {
                array_push($out_put_count, round($new_count - $start_count));
            } else if ($old_count > $new_count) {
                array_push($out_put_count, round($old_count - $start_count));
            }
        } else {
            if ($new_count >= $old_count) {
                $old_count = $new_count;
            } else if ($old_count > $new_count) {
                array_push($out_put_count, round($old_count - $start_count));
                $start_count = $new_count;
                $old_count = $new_count;
            }
        }
    }
    
    return array_sum($out_put_count);
}

//取得機台目前支數
function Get_Device_Now_Count($device_data){
    if (!empty($device_data)) {
        $machine_detail = $device_data[count($device_data) - 1]['machine_detail'];
        if (isset($machine_detail['cnt'])) {
            return $machine_detail['cnt'];
        }
    }
    
    return null;
}

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

    if (!empty($machine_status_S)) {
        $machine_status_S_length = count($machine_status_S);
        if (count($machine_status_S[$machine_status_S_length - 1]['timestamp']) != 2) {
            array_push($machine_status_S[$machine_status_S_length - 1]['timestamp'], $now_time);
        }
    }

    return $machine_status_S;
}

//機台時間
function Device_All_Time($machine_status, $totalTime){
    $time = 0;
    $time_array = [];
    if (!empty($machine_status)) {
        foreach ($machine_status as $key => $value) {
            $time += (strtotime($value['timestamp'][1]) - strtotime($value['timestamp'][0]));
            array_push($time_array, $value['timestamp']);
        }
    }
    $time = round(round($time / $totalTime, 2) * 100);
    return [$time, $time_array];
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
            } else if ($all_time_array_start >= $queue_time_start && $all_time_array_start <= $queue_time_end && $all_time_array_end >= $queue_time_start && $all_time_array_end <= $queue_time_end) {
                array_splice($machine_status_S, $j + 1, 0, array(array('timestamp' => [$all_time_array[$i][1], $machine_status_S[$j]['timestamp'][1]])));
                $machine_status_S[$j]['timestamp'][1] = $all_time_array[$i][0];
            } else if ($all_time_array_start > $queue_time_start && $all_time_array_start < $queue_time_end && $all_time_array_end > $queue_time_start && $all_time_array_end >= $queue_time_end) {
                $machine_status_S[$j]['timestamp'][1] = $all_time_array[$i][0];
            } else if ($all_time_array_start > $queue_time_start && $all_time_array_start > $queue_time_end && $all_time_array_end > $queue_time_start && $all_time_array_end > $queue_time_end) {

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

//陣列裡的第一個元素排序
function sort_first_time($a, $b){
    if(strtotime($a[0]) == strtotime($b[0])) return 0;
    return (strtotime($a[0]) > strtotime($b[0])) ? 1 : -1;
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
                    foreach ($machine_light_abn_data as $machine_light_abn_data_key => $machine_light_abn_data_value) {
                        if ($machine_light_abn_data_value['value'] == $status_detail[$machine_light_abn_data_key]) {
                            if ($machine_light_abn_data_key == 'in_lube') {
                                if ($status_detail['OPR'] == 1) {
                                    $status_detail['err_data'] = true;
                                    array_push($machine_abn_id, $machine_light_abn_data_value['err_code']);
                                    array_push($machine_abn_description, $machine_light_abn_data_value['description']);
                                }
                            } else {
                                $status_detail['err_data'] = true;
                                array_push($machine_abn_id, $machine_light_abn_data_value['err_code']);
                                array_push($machine_abn_description, $machine_light_abn_data_value['description']);
                            }
                            // $status_detail['err_data'] = true;
                            // array_push($machine_abn_id, $machine_abn_data_value['err_code']);
                            // array_push($machine_abn_description, $machine_abn_data_value['description']);
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
                    foreach ($machine_light_abn_data as $machine_light_abn_data_key => $machine_light_abn_data_value) {
                        if ($machine_light_abn_data_key != 'in_lube') {
                            if ($machine_light_abn_data_value['value'] == $status_detail[$machine_light_abn_data_key]) {
                                $status_detail['err_data'] = true;
                                array_push($machine_abn_id, $machine_light_abn_data_value['err_code']);
                                array_push($machine_abn_description, $machine_light_abn_data_value['description']);
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

//查詢工單相關基本資料與檢驗資料
function query_workorder_detail($device_name, $work_code, $project){
    $fields = new stdClass();
    $fields->work_order = ["code", "work_qty", "control_card", "org_code", "commodity_code"];
    $fields->v_cd_sp = "";
    // $fields->commodity = ["code", "standard_weight", "chinese_name", "material_weight"];//material_weight需要改成梅花塊，標準單支+梅花塊=原料重量，若梅花塊=0，則標準單支*1.15=原料重量
    $fields->wire_box = ["code", "chinese_name"];
    // $fields->project = ["id", "name"];
    // $fields->check = ['code','chinese_name'];
    // $fields->category = ['code','name'];
    // $fields->commodity_specification = ["value"];
    $join = new stdClass();
    $join->work_order = [];
    // $commodity = new stdClass();
    // $commodity->commodity = new stdClass();
    // $commodity->commodity->commodity_code = new stdClass();
    // $commodity->commodity->commodity_code = "code";
    // $commodity->commodity->JOIN = new stdClass();
    // $commodity->commodity->JOIN->commodity_specification = new stdClass();
    // $commodity->commodity->JOIN->commodity_specification->id = new stdClass();
    // $commodity->commodity->JOIN->commodity_specification->id = "commodity_id";
    // $commodity->commodity->JOIN->commodity_specification->JOIN = new stdClass();
    // $commodity->commodity->JOIN->commodity_specification->JOIN->project = new stdClass();
    // $commodity->commodity->JOIN->commodity_specification->JOIN->project->project_id = new stdClass();
    // $commodity->commodity->JOIN->commodity_specification->JOIN->project->project_id = "id";
    // $commodity->commodity->JOIN->commodity_specification->JOIN->category = new stdClass();
    // $commodity->commodity->JOIN->commodity_specification->JOIN->category->category_id = new stdClass();
    // $commodity->commodity->JOIN->commodity_specification->JOIN->category->category_id = "id";
    // $commodity->commodity->JOIN->commodity_specification->JOIN->check = new stdClass();
    // $commodity->commodity->JOIN->commodity_specification->JOIN->check->check_id = new stdClass();
    // $commodity->commodity->JOIN->commodity_specification->JOIN->check->check_id = "id";
    $v_cd_sp = new stdClass();
    $v_cd_sp->v_cd_sp = new stdClass();
    $v_cd_sp->v_cd_sp->commodity_code = new stdClass();
    $v_cd_sp->v_cd_sp->commodity_code = "org_code";
    $wire_box = new stdClass();
    $wire_box->wire_box = new stdClass();
    $wire_box->wire_box->wire_code = new stdClass();
    $wire_box->wire_box->wire_code = "code";
    array_push($join->work_order, $v_cd_sp);
    array_push($join->work_order, $wire_box);
    $symbols = new stdClass();
    $symbols->work_order = new stdClass();
    $symbols->work_order->code = ['equal'];
    // $symbols->project = new stdClass();
    // $symbols->project->id = ['equal'];
    $whereAttr = new stdClass();
    $whereAttr->work_order = new stdClass();
    $whereAttr->work_order->code = [$work_code];
    // $whereAttr->project = new stdClass();
    // $whereAttr->project->id = [$project];
    $tables = ['work_order', 'v_cd_sp', 'wire_box'];
    $jointype = new stdClass();
    $jointype->work_order_v_cd_sp= "inner";
    // $jointype->commodity_commodity_specification= "inner";
    // $jointype->commodity_specification_project= "inner";
    // $jointype->commodity_specification_category= "inner";
    // $jointype->commodity_specification_check= "inner";
    $jointype->work_order_wire_box= "inner";
    $data = array(
        'condition_1' => array(
            'fields' => $fields,
            'join' => $join,
            'jointype' => $jointype,
            'tables' => $tables,
            'limit' => [0,20],
            'where' => $whereAttr,
            'symbols' => $symbols
        )
    );
    $back_data = CommonSqlSyntaxJoin_Query($data, "MsSQL");
    if ($back_data['Response'] !== 'ok') {
        return [[],[],[],[]];
    } else if (count($back_data['QueryTableData']) == 0) {
        return [[$workorder_detail = array(
            'commodity_chinese_name' => '-',
            'commodity_code' => '-',
            'material_weight' => '-',
            'standard_weight' => '-',
            'wire_chinese_name' => '-',
            'wire_code' => '-',
            'work_code' => '-',
            'work_org_code' => '-',
            'control_card' => '-',
            'work_qty' => '-'
        )],[],[],[]];
    }
    $back_data_SQL = $back_data['SqlSyntax'];
    $back_data_time = $back_data['OperationTime'];
    $back_data = $back_data['QueryTableData'];
    $specification = [];
    for ($i=0; $i < count($back_data); $i++) { 
        if ($i == 0) {
            $workorder_detail = array(
                'commodity_chinese_name' => $back_data[$i]['v_cd_sp$cd_name'],
                'commodity_code' => $back_data[$i]['work_order$commodity_code'],
                'material_weight' => round($back_data[$i]['v_cd_sp$plum_weight'] > 0 ? $back_data[$i]['v_cd_sp$standard_weight'] + $back_data[$i]['v_cd_sp$plum_weight'] : $back_data[$i]['v_cd_sp$standard_weight'] * 1.15, 2),
                'standard_weight' => $back_data[$i]['v_cd_sp$standard_weight'],
                'wire_chinese_name' => $back_data[$i]['wire_box$chinese_name'],
                'wire_code' => $back_data[$i]['wire_box$code'],
                'work_code' => $back_data[$i]['work_order$code'],
                'work_org_code' => $back_data[$i]['work_order$org_code'],
                'control_card' => $back_data[$i]['work_order$control_card'],
                'work_qty' => $back_data[$i]['work_order$work_qty']
            );

            foreach (json_decode($back_data[$i]['v_cd_sp$op_json'], true) as $process => $insp_data) {
                //製程代號
                $this_process = 0;
                //製程與對應的檢驗項目
                if ($process == '打頭') {
                    $this_process = 5;
                } else if ($process == '輾牙') {
                    $this_process = 6;
                } else  if ($process == '熱處理') {
                    $this_process = 7;
                }

                if ($this_process != 0) {
                    for ($i=0; $i < count($insp_data); $i++) { 
                        $this_specification = array(
                            $insp_data[$i]['檢驗代碼'] => array(
                                'chinese_name' => $insp_data[$i]['檢驗名稱'],
                                'standard' => $insp_data[$i]['檢驗方式'],
                                'standardValue' => $insp_data[$i]['檢驗值']
                            ) 
                        );
                        if (!array_key_exists($this_process, $specification)) {
                            $specification += array(
                                $this_process => $this_specification
                            );
                        } else {
                            $specification[$this_process] += $this_specification;
                        }
                    }
                }
            }
        }
        // //製程名稱
        // $process_name += array(
        //     $back_data[$i]['project$id'] => $back_data[$i]['project$name']
        // );
        // //製程與對應的檢驗項目
        // $this_specification = array(
        //     $back_data[$i]['check$code'] => array(
        //         'chinese_name' => $back_data[$i]['check$chinese_name'],
        //         'standard' => $back_data[$i]['category$code'],
        //         'standardValue' => $back_data[$i]['commodity_specification$value']
        //     ) 
        // );
        // if (!array_key_exists($back_data[$i]['project$id'], $specification)) {
        //     $specification += array(
        //         $back_data[$i]['project$id'] => $this_specification
        //     );
        // } else {
        //     $specification[$back_data[$i]['project$id']] += $this_specification;
        // }
    }
    if (empty($back_data)) {
        $workorder_detail = array(
            'commodity_chinese_name' => '-',
            'commodity_code' => '-',
            'material_weight' => '-',
            'standard_weight' => '-',
            'wire_chinese_name' => '-',
            'wire_code' => '-',
            'work_code' => '-',
            'work_org_code' => '-',
            'control_card' => '-',
            'work_qty' => '-'
        );
    }

    return [[$workorder_detail], $specification, [$back_data_SQL,'time:'.$back_data_time]];
}

// 查詢機台機型
function device_box($device_name){
    $fields = ['name', 'capacity_hr', 'model'];
    $whereAttr = new stdClass();
    $whereAttr->name = [$device_name];
    $symbols = new stdClass();
    $symbols->name = ['equal'];
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
        return [[],[]];
    } else if (count($device_box['QueryTableData']) == 0) {
        return [[],[]];
    }
    return [$device_box['QueryTableData'], [$device_box['SqlSyntax'],'time:'.$device_box['OperationTime']]];
}

// 查詢機台燈號
function machine_status_list($device_model){
    $whereAttr = new stdClass();
    $whereAttr->model = [$device_model];
    $symbols = new stdClass();
    $symbols->model = ['equal'];
    $data = array(
        'condition_1' => array(
            'table' => 'machine_status_list',
            'where' => $whereAttr,
            'symbols' => $symbols
        )
    );
    $machine_status_list = CommonSqlSyntax_Query($data, "MySQL");
    if ($machine_status_list['Response'] !== 'ok') {
        return [[],[]];
    } else if (count($machine_status_list['QueryTableData']) == 0) {
        return [[],[]];
    }
    return [$machine_status_list['QueryTableData'], [$machine_status_list['SqlSyntax'],'time:'.$machine_status_list['OperationTime']]];
}

//取得該機台的燈號異常值
function machine_light_abn_data($machine_light_list_data, $machine_abn_data){
    $machine_light_abn_data = array();
    foreach ($machine_light_list_data as $machine_light_list_data_key => $machine_light_list_data_value) {
        foreach ($machine_abn_data as $machine_abn_data_key => $machine_abn_data_value) {
            if ($machine_light_list_data_key == $machine_abn_data_key) {
                $machine_light_abn_data[$machine_abn_data_key] = $machine_abn_data_value;
            }
        }
    }
    return $machine_light_abn_data;
}

//機台狀態
function Get_device_status($machine_on_off_hist_data, $machine_device_data, $machine_light_abn_data, $process){
    $device_status;
    if ($machine_on_off_hist_data[count($machine_on_off_hist_data) - 1]['status'] == 'E') {
        $device_status = 'S';
    }
    if (!isset($device_status) && $machine_device_data[0]['machine_detail'] != "") {
        $machine_detail = $machine_device_data[0]['machine_detail'];
        if ($machine_detail['OPR'] == 1) {
            $device_status = 'R';//運轉
        } else {
            $device_status = 'Q';//閒置
        }
        if ($process == 5) {
            foreach ($machine_light_abn_data as $machine_light_abn_data_key => $machine_light_abn_data_value) {
                if ($machine_light_abn_data_value['value'] == $machine_detail[$machine_light_abn_data_key]) {
                    if ($machine_light_abn_data_key == 'in_lube') {
                        if ($machine_detail['OPR'] == 1) {
                            $device_status = 'H';
                        break;
                        }
                    } else {
                        $device_status = 'H';
                    break;
                    }
                }
            }
        } else if ($process == 6) {
            foreach ($machine_light_abn_data as $machine_light_abn_data_key => $machine_light_abn_data_value) {
                if ($machine_light_abn_data_key != 'in_lube') {
                    if ($machine_light_abn_data_value['value'] == $machine_detail[$machine_light_abn_data_key]) {
                        $device_status = 'H';
                    break;
                    }
                }
            }
        }
    } else {
        $device_status = 'S';
    }
    return $device_status;
}

//查詢工單上線資料
function work_code_use($device_name, $work_code, $process){
    $whereAttr = new stdClass();
    $whereAttr->device_name = [$device_name];
    $whereAttr->work_code = [$work_code];
    $whereAttr->project_id = [$process];
    $symbols = new stdClass();
    $symbols->device_name = ['equal'];
    $symbols->work_code = ['equal'];
    $symbols->project_id = ['equal'];
    $data = array(
        'condition_1' => array(
            'fields' => ['upload_at', 'work_code', 'project_id', 'device_name', 'status'],
            'table' => 'work_code_use',
            'orderby' => ['desc','upload_at'],
            'limit' => [0,2],
            'symbols' => $symbols,
            'where' => $whereAttr,
        )
    );
    $work_code_use = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    if ($work_code_use['Response'] !== 'ok') {
        return [[],[[],'']];
    } else if (count($work_code_use['QueryTableData']) == 0) {
        return [[],[[],'']];
    }
    return [array_reverse($work_code_use['QueryTableData']),[$work_code_use['SqlSyntax'],'time:'.$work_code_use['OperationTime']]];
}

//查詢模具資料
function mould_series_no_use($work_code, $wrok_code_start_time){
    $whereAttr = new stdClass();
    $whereAttr->work_code = [$work_code];
    $whereAttr->upload_at = [$wrok_code_start_time];
    $symbols = new stdClass();
    $symbols->work_code = ['equal'];
    $symbols->upload_at = ['greater'];
    $data = array(
        'condition_1' => array(
            'fields' => ['upload_at', 'mould_code', 'mould_series_no', 'work_code', 'status', 'cnt'],
            'table' => 'mould_series_no_use',
            'orderby' => ['asc','upload_at'],
            'limit' => ['ALL'],
            'symbols' => $symbols,
            'where' => $whereAttr,
        )
    );
    $mould_series_no_use = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    if ($mould_series_no_use['Response'] !== 'ok') {
        return [[],[]];
    } else if (count($mould_series_no_use['QueryTableData']) == 0) {
        return [[],[]];
    }
    return [$mould_series_no_use['QueryTableData'], [$mould_series_no_use['SqlSyntax'],'time:'.$mould_series_no_use['OperationTime']]];
}

//查詢牙板資料
function thread_series_no_use($work_code, $wrok_code_start_time){
    $whereAttr = new stdClass();
    $whereAttr->work_code = [$work_code];
    $whereAttr->upload_at = [$wrok_code_start_time];
    $symbols = new stdClass();
    $symbols->work_code = ['equal'];
    $symbols->upload_at = ['greater'];
    $data = array(
        'condition_1' => array(
            'fields' => ['upload_at', 'thread_code', 'thread_series_no', 'work_code', 'status', 'cnt'],
            'table' => 'thread_series_no_use',
            'orderby' => ['asc','upload_at'],
            'limit' => ['ALL'],
            'symbols' => $symbols,
            'where' => $whereAttr,
        )
    );
    $thread_series_no_use = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    if ($thread_series_no_use['Response'] !== 'ok') {
        return [[],[]];
    } else if (count($thread_series_no_use['QueryTableData']) == 0) {
        return [[],[]];
    }
    return [$thread_series_no_use['QueryTableData'], [$thread_series_no_use['SqlSyntax'],'time:'.$thread_series_no_use['OperationTime']]];
}

//查詢線材資料
function wire_scroll_no_use($work_code, $wrok_code_start_time){
    $whereAttr = new stdClass();
    $whereAttr->work_code = [$work_code];
    $whereAttr->upload_at = [$wrok_code_start_time];
    $symbols = new stdClass();
    $symbols->work_code = ['equal'];
    $symbols->upload_at = ['greater'];
    $data = array(
        'condition_1' => array(
            'fields' => ['upload_at', 'scroll_no', 'work_code', 'status', 'weight'],
            'table' => 'wire_scroll_no_use',
            'orderby' => ['asc','upload_at'],
            'limit' => ['ALL'],
            'symbols' => $symbols,
            'where' => $whereAttr,
        )
    );
    $wire_scroll_no_use = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    if ($wire_scroll_no_use['Response'] !== 'ok') {
        return [[],[]];
    } else if (count($wire_scroll_no_use['QueryTableData']) == 0) {
        return [[],[]];
    }
    return [$wire_scroll_no_use['QueryTableData'], [$wire_scroll_no_use['SqlSyntax'],'time:'.$wire_scroll_no_use['OperationTime']]];
}

//查詢檢測資料
function inspection($work_code, $process, $wrok_code_start_time){
    $whereAttr = new stdClass();
    $symbols = new stdClass();
    if (gettype($work_code) == 'array') {
        $whereAttr->work_code = $work_code;
        $symbols->work_code = [];
        for ($i=0; $i < count($work_code); $i++) { 
            array_push($symbols->work_code, 'equal');
        }
    } else if (gettype($work_code) == 'string') {
        $whereAttr->work_code = [$work_code];
        $symbols->work_code = ['equal'];
    }
    $whereAttr->project_id = [$process];
    $whereAttr->upload_at = [$wrok_code_start_time];
    $symbols->project_id = ['equal'];
    $symbols->upload_at = ['greater'];
    $data = array(
        'condition_1' => array(
            'fields' => ['upload_at', 'work_code', 'project_id', 'inspection_detail', 'result'],
            'intervaltime' => array('upload_at' => [[date("Y-m-d H:i:s", strtotime(date("Y-m-d H:i:s"))-172800), date("Y-m-d H:i:s")]]),
            'table' => 'inspection',
            'orderby' => ['desc','upload_at'],
            'limit' => ['ALL'],
            'symbols' => $symbols,
            'where' => $whereAttr,
        )
    );
    $inspection = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    if ($inspection['Response'] !== 'ok') {
        return [[],[]];
    } else if (count($inspection['QueryTableData']) == 0) {
        return [[],[]];
    }
    return [$inspection['QueryTableData'], [$inspection['SqlSyntax'],'time:'.$inspection['OperationTime']]];
}

//查詢工時
function workhour($work_code, $process, $wrok_code_start_time){
    $whereAttr = new stdClass();
    $symbols = new stdClass();
    if (gettype($work_code) == 'array') {
        $whereAttr->work_code = $work_code;
        $symbols->work_code = [];
        for ($i=0; $i < count($work_code); $i++) { 
            array_push($symbols->work_code, 'equal');
        }
    } else if (gettype($work_code) == 'string') {
        $whereAttr->work_code = [$work_code];
        $symbols->work_code = ['equal'];
    }
    $whereAttr->project_id = [$process];
    $whereAttr->upload_at = [$wrok_code_start_time];
    $symbols->project_id = ['equal'];
    $symbols->upload_at = ['greater'];
    $data = array(
        'condition_1' => array(
            'fields' => ['upload_at', 'work_code', 'project_id', 'status'],
            'table' => 'workhour',
            'orderby' => ['desc','upload_at'],
            'limit' => [0,1],
            'symbols' => $symbols,
            'where' => $whereAttr,
        )
    );
    $workhour = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    if ($workhour['Response'] !== 'ok') {
        return [[],[]];
    } else if (count($workhour['QueryTableData']) == 0) {
        return [[],[]];
    }
    return [$workhour['QueryTableData'], [$workhour['SqlSyntax'],'time:'.$workhour['OperationTime']]];
}

//查詢流程卡-桶重
function runcard($work_code, $process, $wrok_code_start_time){
    $whereAttr = new stdClass();
    $symbols = new stdClass();
    if (gettype($work_code) == 'array') {
        $whereAttr->runcard_code = $work_code;
        $symbols->runcard_code = [];
        for ($i=0; $i < count($work_code); $i++) { 
            array_push($symbols->runcard_code, 'like');
        }
    } else if (gettype($work_code) == 'string') {
        $whereAttr->runcard_code = [$work_code];
        $symbols->runcard_code = ['like'];
    }
    $whereAttr->project_id = [$process];
    $whereAttr->upload_at = [$wrok_code_start_time];
    $symbols->project_id = ['equal'];
    $symbols->upload_at = ['greater'];
    $data = array(
        'condition_1' => array(
            'fields' => ['upload_at', 'runcard_code', 'project_id', 'furnace_code', 'screw_weight'],
            'table' => 'runcard',
            'orderby' => ['asc','upload_at'],
            'limit' => ['ALL'],
            'symbols' => $symbols,
            'where' => $whereAttr,
        )
    );
    $runcard = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    if ($runcard['Response'] !== 'ok') {
        return [[],[]];
    } else if (count($runcard['QueryTableData']) == 0) {
        return [[],[]];
    }
    return [$runcard['QueryTableData'], [$runcard['SqlSyntax'],'time:'.$runcard['OperationTime']]];
}

//輾牙機台目前支數
function get_start_count($device_name, $wrok_code_start_time, $device_now_count){
    $whereAttr = new stdClass();
    $symbols = new stdClass();
    $whereAttr->upload_at = [$wrok_code_start_time];
    $symbols->upload_at = ['greater'];
    $data = array(
        'condition_1' => array(
            'table' => strtolower($device_name),
            'orderby' => ['asc','upload_at'],
            'limit' => [0,1],
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

//查詢線材名稱、支架重
function wire_stack($wire_code_array){
    $whereAttr = new stdClass();
    $whereAttr->scroll_no = $wire_code_array;
    $symbols = new stdClass();
    $symbols->scroll_no = [];
    for ($i=0; $i < count($wire_code_array); $i++) { 
        array_push($symbols->scroll_no, 'equal');
    }
    $data = array(
        'condition_1' => array(
            'fields' => ['scroll_no', 'furnace_code', 'rack_wgt'],
            'table' => 'wire_stack',
            'limit' => ['ALL'],
            'symbols' => $symbols,
            'where' => $whereAttr,
        )
    );
    $wire_stack = CommonSqlSyntax_Query($data, "MsSQL");
    if ($wire_stack['Response'] !== 'ok') {
        return [[],[]];
    } else if (count($wire_stack['QueryTableData']) == 0) {
        return [[],[]];
    }
    return [$wire_stack['QueryTableData'], [$wire_stack['SqlSyntax'],'time:'.$wire_stack['OperationTime']]];
}

//線材使用資訊
function wire_use_information($wire_scroll_no_use_data, $material_total_weight, $wire_now_scroll_no){
    $wire_use_data = [];
    $wire_code_array = [];
    foreach ($wire_scroll_no_use_data as $key => $value) {
        if (!in_array($value['scroll_no'], $wire_code_array)) {
            array_push($wire_code_array, $value['scroll_no']);
            array_push($wire_use_data, array(
                'scroll_no' => $value['scroll_no'],
                'status' => $value['status'],
                'weight' => $value['weight'],
                'back' => false
            ));
        } else {
            $this_position = array_search($value['scroll_no'], $wire_code_array);
            if ($value['status'] == 'S') {
                $wire_use_data[$this_position]['weight'] += $value['weight'];
                $wire_use_data[$this_position]['back'] = false;
            } else if ($value['status'] == 'E') {
                $wire_use_data[$this_position]['weight'] -= $value['weight'];
                $wire_use_data[$this_position]['back'] = true;
            }
        }
    }
    
    $wire_now_scroll_no_rack_wgt = 0;
    if (count($wire_code_array) > 0) {
        $wire_furnace_code = array();
        [$wire_stack_data, $wire_stack_SQL] = wire_stack($wire_code_array);
        foreach ($wire_stack_data as $key => $value) {
            $wire_furnace_code[$value['scroll_no']] = $value['furnace_code'];
            if (isset($wire_now_scroll_no)) {
                if ($value['scroll_no'] == $wire_now_scroll_no) {
                    $wire_now_scroll_no_rack_wgt = $value['rack_wgt'];
                }
            }
        }
    }
    
    $wire_use_information = array();
    $wire_total_weight = 0;
    $wire_loss_rate = 0;
    foreach ($wire_use_data as $key => $value) {
        if ($value['back']) {
            array_push($wire_use_information, array(
                'scroll_no' => $value['scroll_no'],
                'furnaceCode' => $wire_furnace_code[$value['scroll_no']],
                'consumption' => $value['weight'] < 0 ? '-' : $value['weight'],
                'attrition' => '-',
            ));
            $wire_total_weight += $value['weight'];
        } else {
            array_push($wire_use_information, array(
                'scroll_no' => $value['scroll_no'],
                'furnaceCode' => isset($wire_furnace_code[$value['scroll_no']])?$wire_furnace_code[$value['scroll_no']]:'--',
                'consumption' => '上線中',
                'attrition' => '-',
            ));
        }
    }
    if ($wire_total_weight > 0) {
        $wire_loss_rate = round((($wire_total_weight - $material_total_weight) / $wire_total_weight) * 100, 3);
        if ($wire_loss_rate < 0) {
            $wire_loss_rate = 0;
        }
    } else {
        $wire_total_weight = 0;
    }
    return [$wire_use_information, $wire_total_weight, $wire_loss_rate, $wire_now_scroll_no_rack_wgt, empty($wire_stack_SQL)?[]:$wire_stack_SQL];
}

//查詢模具名稱
function mould($mould_code_array){
    $whereAttr = new stdClass();
    $whereAttr->code = [$mould_code_array];
    $symbols = new stdClass();
    $symbols->code = ['in'];
    $data = array(
        'condition_1' => array(
            'fields' => ['code', 'chinese_name'],
            'table' => 'mould',
            'limit' => ['ALL'],
            'symbols' => $symbols,
            'where' => $whereAttr,
        )
    );
    $mould = CommonSqlSyntax_Query($data, "MsSQL");
    if ($mould['Response'] !== 'ok') {
        return [[],[]];
    } else if (count($mould['QueryTableData']) == 0) {
        return [[],[]];
    }
    return [$mould['QueryTableData'], [$mould['SqlSyntax'],'time:'.$mould['OperationTime']]];
}

//使用模具
function mold_use_information($mould_series_no_use_data){
    $mold_use_data = [];
    $mould_code_array = [];
    foreach ($mould_series_no_use_data as $key => $value) {
        if (!in_array($value['mould_code'], $mould_code_array)) {
            array_push($mould_code_array, $value['mould_code']);
        }
    }
    [$mould_data, $mould_SQL] = mould($mould_code_array);

    foreach ($mould_series_no_use_data as $mould_series_no_use_key => $mould_series_no_use_value) {
        if ($mould_series_no_use_value['status'] == 'S') {
            foreach ($mould_data as $mould_key => $mould_value) {
                if ($mould_series_no_use_value['mould_code'] == $mould_value['code']) {
                    array_push($mold_use_data, array(
                        'code' => $mould_series_no_use_value['mould_code'],
                        'seriesNo' => $mould_series_no_use_value['mould_series_no'],
                        'name' => $mould_value['chinese_name'],
                    ));
                }
            }
        }
    }

    return [$mold_use_data, $mould_SQL,$mould_data];
}

//使用牙板
function thread_use_information($thread_series_no_use_data){
    $thread_use_data = [];
    $mould_code_array = [];
    foreach ($thread_series_no_use_data as $key => $value) {
        if (!in_array($value['thread_code'], $mould_code_array)) {
            array_push($mould_code_array, $value['thread_code']);
        }
    }
    [$mould_data, $mould_SQL] = mould($mould_code_array);

    foreach ($thread_series_no_use_data as $thread_series_no_use_key => $thread_series_no_use_value) {
        if ($thread_series_no_use_value['status'] == 'S') {
            foreach ($mould_data as $mould_key => $mould_value) {
                if ($thread_series_no_use_value['thread_code'] == $mould_value['code']) {
                    array_push($thread_use_data, array(
                        'code' => $thread_series_no_use_value['thread_code'],
                        'seriesNo' => $thread_series_no_use_value['thread_series_no'],
                        'name' => $mould_value['chinese_name'],
                    ));
                }
            }
        }
    }

    return [$thread_use_data, $mould_SQL,$mould_data];
}

//每桶產出
function bucket_use_information($runcard_data){
    $bucket_use_data = [];
    foreach ($runcard_data as $key => $value) {
        array_push($bucket_use_data, array(
            'code' => $value['runcard_code'],
            'furnaceCode' => $value['furnace_code'],
            'screwWeight' => $value['screw_weight']
        ));
    }
    return $bucket_use_data;
}

//檢驗數據
function inspection_use_information($specification_data, $inspection_data, $standard_weight){
    if (!is_numeric($standard_weight)) {
        $standard_weight = 0;
    }
    $total_inspection_data = [];
    if (!empty($specification_data) && !empty($inspection_data)) {
        for ($i=0; $i < count($inspection_data); $i++) {
            $inspection_detail = $inspection_data[$i]['inspection_detail'];
            if (is_string($inspection_detail)) {
                $inspection_detail = json_decode($inspection_detail, true);
            }
            $this_inspection = [];//紀錄該筆檢驗資料
            foreach ($specification_data[$inspection_data[$i]['project_id']] as $check_code => $value) {
                $standardValue = "";
                if ($value['standard'] == 'BETWEEN') {
                    $this_process_check_standard_value = explode("~",$value['standardValue']);
    
                    $standardValue = $this_process_check_standard_value[0] . '~' . $this_process_check_standard_value[1];
                } else if ($value['standard'] == 'MIN') {
                    $standardValue = '≧' . $value['standardValue'];
                } else if ($value['standard'] == 'MAX') {
                    $standardValue = '≦' . $value['standardValue'];
                } else if ($value['standard'] == 'TOOL') {
                    $standardValue = $value['standardValue'];
                }
    
                if (isset($inspection_detail[$check_code])) {
                    array_push($this_inspection, array(
                        'code' => $value['chinese_name'],
                        'standardValue' => $standardValue,
                        'inspectionValue' => $inspection_detail[$check_code]['value'],
                        'result' => $inspection_detail[$check_code]['result']==1?'PASS':'NG'
                    ));
                } else {
                    array_push($this_inspection, array(
                        'code' => $value['chinese_name'],
                        'standardValue' => $standardValue,
                        'inspectionValue' => '--',
                        'result' => '--'
                    ));
                }
            }

            //檢驗單支重
            if (isset($inspection_detail['act_wgt'])) {
                $unit_weight = floatval($inspection_detail['act_wgt']);
                if ($unit_weight != 0) {
                    $unit_range = [round($standard_weight * 0.9, 2), round($standard_weight * 1.1, 2)];

                    if ($unit_range[0] <= $unit_weight && $unit_weight <= $unit_range[1]) {
                        $unit_result = 'PASS';
                    } else {
                        $unit_result = 'NG';
                    }
                    array_push($this_inspection, array(
                        'code' => '單支重',
                        'standardValue' => $unit_range[0] . '~' . $unit_range[1],
                        'inspectionValue' => $unit_weight,
                        'result' => $unit_result
                    ));
                } else {
                    array_push($this_inspection, array(
                        'code' => '單支重',
                        'standardValue' => '--',
                        'inspectionValue' => 0,
                        'result' => '--'
                    ));
                }
            }
    
            array_push($total_inspection_data, array(
                'inspection' => $this_inspection,
                'timestamp' =>$inspection_data[$i]['upload_at']
            ));
        }
    }
    return $total_inspection_data;
}

//總生產時間
function totalProduceTime($device_name, $work_code_use_data, $process_name){
    $totalProduceTime = [];
    for ($i=0; $i < count($work_code_use_data); $i++) { 
        if (in_array($process_name[$work_code_use_data[$i]['project_id']], array_column($totalProduceTime, 'code'))) {
            $work_code_use_dataPosition = array_search($work_code_use_data[$i]['project_id'], array_column($totalProduceTime, 'code'));
            if ($work_code_use_data[$i]['status'] == 'S') {
                if ($totalProduceTime[$work_code_use_dataPosition]['startTime'] == '-') {
                    $totalProduceTime[$work_code_use_dataPosition]['startTime'] = $work_code_use_data[$i]['upload_at'];
                } else {
                    if (strtotime($totalProduceTime[$work_code_use_dataPosition]['startTime']) > strtotime($work_code_use_data[$i]['upload_at'])) {
                        $totalProduceTime[$work_code_use_dataPosition]['startTime'] = $work_code_use_data[$i]['upload_at'];
                    }
                }
                if ($totalProduceTime[$work_code_use_dataPosition]['endTime'] != '-') {
                    if (strtotime($totalProduceTime[$work_code_use_dataPosition]['startTime']) > strtotime($totalProduceTime[$work_code_use_dataPosition]['endTime'])) {
                        $totalProduceTime[$work_code_use_dataPosition]['endTime'] = '-';
                    }
                }
            } else if ($work_code_use_data[$i]['status'] == 'E') {
                if ($totalProduceTime[$work_code_use_dataPosition]['endTime'] == '-') {
                    $totalProduceTime[$work_code_use_dataPosition]['endTime'] = $work_code_use_data[$i]['upload_at'];
                } else {
                    if (strtotime($work_code_use_data[$i]['upload_at']) > strtotime($totalProduceTime[$work_code_use_dataPosition]['endTime'])) {
                        $totalProduceTime[$work_code_use_dataPosition]['endTime'] = $work_code_use_data[$i]['upload_at'];
                    }
                }
            }
        } else {
            if ($work_code_use_data[$i]['status'] == 'S') {
                $totalProduceTime[count($totalProduceTime)] = array(
                    'code' => !empty($process_name) ? $process_name[$work_code_use_data[$i]['project_id']] : '-',
                    'device_name' => $device_name,
                    'startTime' => $work_code_use_data[$i]['upload_at'],
                    'endTime' => '-',
                    'totalTime' => '-',
                );
            } else if ($work_code_use_data[$i]['status'] == 'E') {
                $totalProduceTime[count($totalProduceTime)] = array(
                    'code' => !empty($process_name) ? $process_name[$work_code_use_data[$i]['project_id']] : '-',
                    'device_name' => $device_name,
                    'startTime' => '-',
                    'endTime' => $work_code_use_data[$i]['upload_at'],
                    'totalTime' => '-',
                );
            }
        }
    }
    for ($i=0; $i < count($totalProduceTime); $i++) { 
        $projectWorkRunTime = TimeSubtraction($totalProduceTime[$i]['startTime'], $totalProduceTime[$i]['endTime'], 'hour');
        // $totalProduceTime[$i]['code'] = $process_name[$totalProduceTime[$i]['code']];
        if ($projectWorkRunTime[0]) {
            $totalProduceTime[$i]['totalTime'] = $projectWorkRunTime[0];
        } else {
            $totalProduceTime[$i]['totalTime'] = TimeSubtraction($totalProduceTime[$i]['startTime'], date("Y-m-d H:i:s"), 'hour')[0];
        }
    }
    if (!empty($totalProduceTime)) {
        $totalWorkRunTime = TimeSubtraction($totalProduceTime[0]['startTime'], $totalProduceTime[count($totalProduceTime) - 1]['endTime'], 'date');
        $total_work_time = $totalWorkRunTime[1] . '(' . $totalProduceTime[0]['startTime'] . ' ~ ' . $totalProduceTime[count($totalProduceTime) - 1]['endTime'] . ')';
    } else {
        $total_work_time = '-';
    }

    return [$totalProduceTime, $total_work_time];
}

function machine_model_image($model){
    $whereAttr = new stdClass();
    $whereAttr->model = [$model];
    $symbols = new stdClass();
    $symbols->model = ['equal'];
    $data = array(
        'condition_1' => array(
            'fields' => ['model', 'img_name'],
            'table' => 'machine_model_image',
            'limit' => [0,1],
            'symbols' => $symbols,
            'where' => $whereAttr,
        )
    );
    $machine_model_image = CommonSqlSyntax_Query($data, "MySQL");
    if ($machine_model_image['Response'] !== 'ok') {
        return [[],[]];
    } else if (count($machine_model_image['QueryTableData']) == 0) {
        return [[],[]];
    }
    return [$machine_model_image['QueryTableData'], [$machine_model_image['SqlSyntax'],'time:'.$machine_model_image['OperationTime']]];
}

//機台燈號
function machine_light($machine_detail, $light_list, $machine_abn_data, $device_status){
    $machine_light = [];
    $machine_item = array();
    if ($machine_detail != '') {
        $not_show_key = ['OPR', 'cnt', 'cnt_last', 'timestamp', 'wire_weight'];
        if ($device_status == 'S') {
            foreach ($light_list as $key => $value) {
                foreach ($machine_abn_data as $machine_abn_data_key => $machine_abn_data_value) {
                    if ($key == $machine_abn_data_key) {
                        $machine_item[$key] = array(
                            'value' => 1,
                            'color' => $machine_abn_data_value['value'] == 1 ? 'red' : 'green',
                            'name' => $value,
                        );
                    }
                }
                if (!isset($machine_item[$key])) {
                    $machine_item[$key] = array(
                        'value' => 1,
                        'color' => 'orange',
                        'name' => $value,
                    );
                }
                if (!in_array($key, $not_show_key)) {
                    $machine_light[$key] = 0;
                }
            }
        } else {
            foreach ($light_list as $key => $value) {
                foreach ($machine_abn_data as $machine_abn_data_key => $machine_abn_data_value) {
                    if ($key == $machine_abn_data_key) {
                        $machine_item[$key] = array(
                            'value' => 1,
                            'color' => $machine_abn_data_value['value'] == 1 ? 'red' : 'green',
                            'name' => $value,
                        );
                    }
                }
                if (!isset($machine_item[$key])) {
                    $machine_item[$key] = array(
                        'value' => 1,
                        'color' => 'orange',
                        'name' => $value,
                    );
                }
                foreach ($machine_detail as $machine_detail_key => $machine_detail_value) {
                    if ($key == $machine_detail_key) {
                        if (!in_array($machine_detail_key, $not_show_key)) {
                            $machine_light[$machine_detail_key] = $machine_detail_value;
                        }
                    }
                }
            }
        }
    }
    return [$machine_light, $machine_item];
}

//陣列裡的第一個元素排序
function sort_start_time($a, $b){
    if(strtotime($a['startTime']) == strtotime($b['startTime'])) return 0;
    return (strtotime($a['startTime']) > strtotime($b['startTime'])) ? 1 : -1;
}
//時間是否有交集，有交集則返回該筆交集的最早時間與最晚時間
function is_time_cross($source_begin_time_1 = '', $source_end_time_1 = '', $source_begin_time_2 = '', $source_end_time_2 = '') {
    $beginTime1 = strtotime($source_begin_time_1);
    $endTime1 = strtotime($source_end_time_1);
    $beginTime2 = strtotime($source_begin_time_2);
    $endTime2 = strtotime($source_end_time_2);
    $status = $beginTime2 - $beginTime1;
    if ($status > 0) {
        $status2 = $beginTime2 - $endTime1;
        if ($status2 >= 0) {
            // return false;
            return [];
        } else {
            // return true;
            // add return time
            $status3 = $endTime2 - $endTime1;
            if ($status3 >= 0) {
                return [$source_begin_time_1, $source_end_time_2];
            } else {
                return [$source_begin_time_1, $source_end_time_1];
            }
        }
    } else {
        $status2 = $endTime2 - $beginTime1;
        if ($status2 > 0) {
            // return true;
            // add return time
            $status3 = $endTime2 - $endTime1;
            if ($status3 >= 0) {
                return [$source_begin_time_2, $source_end_time_2];
            } else {
                return [$source_begin_time_2, $source_end_time_1];
            }
        } else {
            // return false;
            return [];
        }
    }
}

function change_time($time, $format) {
    $date = floor($time / 86400);
    $hour = floor($time % 86400 / 3600) + $date * 24;
    $minute = floor($time % 86400 / 60) - $hour * 60;
    $second = floor($time % 86400 % 60);

    $date < 10 ? $showDate = '0' . $date : $showDate = $date;
    $hour < 10 ? $showHour = '0' . $hour : $showHour = $hour;
    $minute < 10 ? $showMinute = '0' . $minute : $showMinute = $minute;
    $second < 10 ? $showSecond = '0' . $second : $showSecond = $second;
    if ($format == 'h:m') {
        return $hour.'時'.$minute.'分';
    } else if ($format == 'h:m:s') {
        return $hour.'時'.$minute.'分'.$second.'秒';
    }
}

//工單履歷
function WorkorderHistory($params){
    //查詢work_code_use
    $intervaltime = new stdClass();
    $intervaltime->upload_at = array([$params->startTime,$params->endTime]);
    $symbols = new stdClass();
    $symbols->combine = array();
    $whereAttr = new stdClass();
    $whereAttr->combine = array();
    
    if (isset($params->workID)) {
        if ($params->workID != "") {//若有輸入的工單編號加入條件
            array_push($whereAttr->combine, array(
                'work_code' => [$params->workID]
            ));
            array_push($symbols->combine, array(
                'work_code' => ["equal"]
            ));
        }
    }
    array_push($whereAttr->combine, array(
        'work_code' => ["subcondition_1"]
    ));
    array_push($symbols->combine, array(
        'work_code' => ["in"]
    ));
    $data = array(
        'condition_1' => array(
            'table' => 'work_code_use',
            'intervaltime' => $intervaltime,
            'where' => $whereAttr,
            'limit' => ["ALL"],
            'orderby' => ['asc', 'upload_at'],
            'symbols' => $symbols,
            'subquery' => array('subcondition_1' => array(
                'fields' => ["work_code"],
                'table' => 'work_code_use',
                'intervaltime' => $intervaltime,
                'where' => array(
                    'device_name' => [$params->deviceID],
                    'status' => ["E"]
                ),
                'limit' => ["ALL"],
                'symbols' => array(
                    'device_name' => ["equal"],
                    'status' => ["equal"]
                )
            ))
        )
    );
    $work_code_use = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    if ($work_code_use['Response'] !== 'ok') {
        return $work_code_use;
    } else if (count($work_code_use['QueryTableData']) == 0) {
        $work_code_use['Response'] = "no data";
        return $work_code_use;
    }
    $work_code_use_data = $work_code_use['QueryTableData'];
    
    //整理工單
    $workIDArray = [];
    $symbolsArray = [];
    $workID_status = array();
    for ($i=0; $i < count($work_code_use_data); $i++) {
        if (!in_array($work_code_use_data[$i]['work_code'], $workIDArray)) {
            array_push($workIDArray, $work_code_use_data[$i]['work_code']);
            array_push($symbolsArray, 'equal');
        }

        if ($work_code_use_data[$i]['status'] == 'S' && $work_code_use_data[$i]['project_id'] == '5') {
            $workID_status[$work_code_use_data[$i]['work_code']] = '打頭';
        } else if ($work_code_use_data[$i]['status'] == 'E' && $work_code_use_data[$i]['project_id'] == '5') {
            $workID_status[$work_code_use_data[$i]['work_code']] = '半裸成品倉';
        } else if ($work_code_use_data[$i]['status'] == 'S' && $work_code_use_data[$i]['project_id'] == '6') {
            $workID_status[$work_code_use_data[$i]['work_code']] = '輾牙';
        } else if ($work_code_use_data[$i]['status'] == 'E' && $work_code_use_data[$i]['project_id'] == '6') {
            $workID_status[$work_code_use_data[$i]['work_code']] = '半裸成品倉';
        } else if ($work_code_use_data[$i]['status'] == 'S' && $work_code_use_data[$i]['project_id'] == '7') {
            $workID_status[$work_code_use_data[$i]['work_code']] = '熱處理';
        } else if ($work_code_use_data[$i]['status'] == 'E' && $work_code_use_data[$i]['project_id'] == '7') {
            $workID_status[$work_code_use_data[$i]['work_code']] = '半裸成品倉';
        }
    }

    //join work_order,commodity
    $fields = new stdClass();
    $fields->work_order = ["code", "status", "work_qty"];
    $fields->v_cd_sp = "";
    $join = new stdClass();
    $join->work_order = [];
    $v_cd_sp = new stdClass();
    $v_cd_sp->v_cd_sp = new stdClass();
    $v_cd_sp->v_cd_sp->commodity_code = new stdClass();
    $v_cd_sp->v_cd_sp->commodity_code = "org_code";
    array_push($join->work_order, $v_cd_sp);
    $tables = ['work_order', 'v_cd_sp'];
    $whereAttr = new stdClass();
    $whereKey = array(
        'factory_id' => '-',
        'group_id' => '-',
        'itemNumber' => array('v_cd_sp', 'org_code'),
        'workID' => array('work_order', 'code')
    );
    $symbols = new stdClass();
    foreach ($whereKey as $key => $value) {
        if (isset($params->{$key})) {
            if ($params->{$key} != "") {
                if (isset($whereAttr->{$value[0]}) != 1) {
                    $whereAttr->{$value[0]} = new stdClass();
                    $symbols->{$value[0]} = new stdClass();
                }
                $whereAttr->{$value[0]}->{$value[1]} = [$params->{$key}];
                $symbols->{$value[0]}->{$value[1]} = ["equal"];
            }
        } else {
            if ($key == 'workID') {
                $whereAttr->work_order = new stdClass();
                $symbols->work_order = new stdClass();
                $whereAttr->work_order->code = $workIDArray;
                $symbols->work_order->code = $symbolsArray;
            }
        }
    }
    $tables = ['work_order', 'v_cd_sp'];
    $jointype = new stdClass();
    $jointype->work_order_v_cd_sp= "inner";
    $data = array(
        'condition_1' => array(
            'fields' => $fields,
            'join' => $join,
            'jointype' => $jointype,
            'tables' => $tables,
            'where' => $whereAttr,
            'symbols' => $symbols
        )
    );
    $workorder_related = CommonSqlSyntaxJoin_Query($data, "MsSQL");
    
    if($workorder_related['Response'] !== 'ok'){
        return $workorder_related;
    } else if (count($workorder_related['QueryTableData']) == 0) {
        // $workorder_related['Response'] = "no data";
        // return $workorder_related;
    }
    $workorder_related_data = $workorder_related['QueryTableData'];
    
    $returnData['QueryTableData'] = array();
    for ($i=0; $i < count($work_code_use_data); $i++) { 
        $position = array_search($work_code_use_data[$i]['work_code'], array_column($returnData['QueryTableData'], 'workID'));
        if (gettype($position) == 'integer') {
            $completion_date = '--';
            if ($work_code_use_data[$i]['status'] == 7) {
                if ($workID_status[$work_code_use_data[$i]['work_code']] == '半裸成品倉') {
                    $completion_date = $work_code_use_data[$i]['upload_at'];
                }
            }
            $returnData['QueryTableData'][$position]['completion_date'] = $completion_date;
        } else {
            // $no_match_work_code = 0;
            for ($j=0; $j < count($workorder_related_data); $j++) { 
                if ($work_code_use_data[$i]['work_code'] === $workorder_related_data[$j]['work_order$code']) {
                    $completion_date = '--';
                    if ($work_code_use_data[$i]['status'] == 7) {
                        if ($workID_status[$work_code_use_data[$i]['work_code']] == '半裸成品倉') {
                            $completion_date = $work_code_use_data[$i]['upload_at'];
                        }
                    }
                    array_push($returnData['QueryTableData'], array(
                        'workID' => $work_code_use_data[$i]['work_code'],
                        'processSchedule' => $workID_status[$work_code_use_data[$i]['work_code']],
                        'product_name_chinese' => $workorder_related_data[$j]['v_cd_sp$cd_name'],
                        'work_qty' => $workorder_related_data[$j]['work_order$work_qty'],
                        'completion_date' => $completion_date
                    ));
                } else {
                    // $no_match_work_code++;
                }
            }
            // if ($no_match_work_code == count($workorder_related_data)) {
            //     $completion_date = '--';
            //     if ($work_code_use_data[$i]['status'] == 7) {
            //         if ($workID_status[$work_code_use_data[$i]['work_code']] == '半裸成品倉') {
            //             $completion_date = $work_code_use_data[$i]['upload_at'];
            //         }
            //     }
            //     array_push($returnData['QueryTableData'], array(
            //         'workID' => $work_code_use_data[$i]['work_code'],
            //         'processSchedule' => $workID_status[$work_code_use_data[$i]['work_code']],
            //         'product_name_chinese' => '--',
            //         'work_qty' => '--',
            //         'completion_date' => $completion_date
            //     ));
            // }
        }
    }
    $returnData['Response'] = 'ok';
    
    return $returnData;
}

//工單履歷詳細資料
function QueryWorkId($params)//主要查詢按鈕
{
    $workID = $params->workID;

    //join work_order,commodity,wire_box
    $fields = new stdClass();
    $fields->work_order = ["code", "status", "org_code", "work_qty", "wire_code", "control_card", "commodity_code", "mould_code", "source_wgt"];
    $fields->v_cd_sp = "";
    $fields->wire_box = ["chinese_name"];
    $join = new stdClass();
    $join->work_order = [];
    $v_cd_sp = new stdClass();
    $v_cd_sp->v_cd_sp = new stdClass();
    $v_cd_sp->v_cd_sp->commodity_code = new stdClass();
    $v_cd_sp->v_cd_sp->commodity_code = "org_code";
    $wire_box = new stdClass();
    $wire_box->wire_box = new stdClass();
    $wire_box->wire_box->wire_code = new stdClass();
    $wire_box->wire_box->wire_code = "code";
    array_push($join->work_order, $v_cd_sp);
    array_push($join->work_order, $wire_box);
    $symbols = new stdClass();
    $symbols->work_order = new stdClass();
    $symbols->work_order->code = ["equal"];
    $tables = ['work_order', 'v_cd_sp', 'wire_box'];
    $whereAttr = new stdClass();
    $whereAttr->work_order = new stdClass();
    $whereAttr->work_order->code = [$workID];//輸入的工單編號
    $jointype = new stdClass();
    $jointype->work_order_v_cd_sp= "inner";
    $jointype->work_order_wire_box= "inner";
    $data = array(
        'condition_1' => array(
            'fields' => $fields,
            'join' => $join,
            'jointype' => $jointype,
            'tables' => $tables,
            'where' => $whereAttr,
            'symbols' => $symbols
        )
    );
    $workorder_related = CommonSqlSyntaxJoin_Query($data, "MsSQL");
  
    if ($workorder_related['Response'] !== 'ok') {
        return $workorder_related;
    } else if (count($workorder_related['QueryTableData']) == 0) {
        // $workorder_related['Response'] = "no data";
        // return $workorder_related;
    }
    $workorder_related_data = $workorder_related['QueryTableData'];

    //查詢work_code_use
    $symbols = new stdClass();
    $symbols->work_code = ["equal"];
    $whereAttr = new stdClass();
    $whereAttr->work_code = [$workID];//輸入的工單編號
    $data = array(
        'condition_1' => array(
            'table' => 'work_code_use',
            'where' => $whereAttr,
            'limit' => ["ALL"],
            'symbols' => $symbols
        )
    );
    $work_code_use = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");

    if ($work_code_use['Response'] !== 'ok') {
        return $work_code_use;
    } else if (count($work_code_use['QueryTableData']) == 0) {
        // $work_code_use['Response'] = "no data";
        // return $work_code_use;
    }
    $work_code_use_data = $work_code_use['QueryTableData'];

    $project_array = [];
    for ($i=0; $i < count($work_code_use_data); $i++) { 
        array_push($project_array, $work_code_use_data[$i]['project_id']);
        $project_array = array_unique($project_array);
    }

    //查詢mould_series_no_use
    $symbols = new stdClass();
    $symbols->work_code = ["equal"];
    $symbols->status = ["equal"];
    $whereAttr = new stdClass();
    $whereAttr->work_code = [$workID];//輸入的工單編號
    $whereAttr->status = ["S"];//輸入的工單狀態
    $data = array(
        'condition_1' => array(
            'table' => 'mould_series_no_use',
            'where' => $whereAttr,
            'limit' => ["ALL"],
            'symbols' => $symbols
        )
    );
    $mould_series_no_use = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    
    if ($mould_series_no_use['Response'] !== 'ok') {
        return $mould_series_no_use;
    } else if (count($mould_series_no_use['QueryTableData']) == 0) {
        // $mould_series_no_use['Response'] = "no data";
        // return $mould_series_no_use;
    }
    $mould_series_no_use_data = $mould_series_no_use['QueryTableData'];

    $mould_code = [];
    $mould_code_symbols = [];
    foreach ($mould_series_no_use_data as $key => $value) {
        if (!in_array($value['mould_code'], $mould_code)) {
            array_push($mould_code, $value['mould_code']);
            array_push($mould_code_symbols, "equal");
        }
    }

    //查詢thread_series_no_use
    $symbols = new stdClass();
    $symbols->work_code = ["equal"];
    $symbols->status = ["equal"];
    $whereAttr = new stdClass();
    $whereAttr->work_code = [$workID];//輸入的工單編號
    $whereAttr->status = ["S"];//輸入的工單狀態
    $data = array(
        'condition_1' => array(
            'table' => 'thread_series_no_use',
            'where' => $whereAttr,
            'limit' => ["ALL"],
            'symbols' => $symbols
        )
    );
    $thread_series_no_use = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    
    if ($thread_series_no_use['Response'] !== 'ok') {
        return $thread_series_no_use;
    } else if (count($thread_series_no_use['QueryTableData']) == 0) {
        // $thread_series_no_use['Response'] = "no data";
        // return $thread_series_no_use;
    }
    $thread_series_no_use_data = $thread_series_no_use['QueryTableData'];

    foreach ($thread_series_no_use_data as $key => $value) {
        if (!in_array($value['thread_code'], $mould_code)) {
            array_push($mould_code, $value['thread_code']);
            array_push($mould_code_symbols, "equal");
        }
    }

    // //查詢material_batch_no_use
    // $symbols = new stdClass();
    // $symbols->work_code = ["equal"];
    // $symbols->status = ["equal"];
    // $whereAttr = new stdClass();
    // $whereAttr->work_code = [$workID];//輸入的工單編號
    // $whereAttr->status = ["S"];//輸入的工單狀態
    // $data = array(
    //     'condition_1' => array(
    //         'table' => 'material_batch_no_use',
    //         'where' => $whereAttr,
    //         'limit' => ["ALL"],
    //         'symbols' => $symbols
    //     )
    // );
    // $material_batch_no_use = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    // if ($material_batch_no_use['Response'] !== 'ok') {
    //     return $material_batch_no_use;
    // } else if (count($material_batch_no_use['QueryTableData']) == 0) {
    //     $material_batch_no_use['Response'] = "no data";
    //     // 暫時不做耗材
    //     // return $material_batch_no_use;
    // }
    // $material_batch_no_use_data = $material_batch_no_use['QueryTableData'];

    // foreach ($material_batch_no_use_data as $key => $value) {
    //     if (!in_array($value['materia_code'], $mould_code)) {
    //         array_push($mould_code, $value['materia_code']);
    //         array_push($mould_code_symbols, "equal");
    //     }
    // }

    //查詢模具名稱
    if (!empty($mould_code)) {
        $whereAttr = new stdClass();
        $whereAttr->code = $mould_code;
        $symbols = new stdClass();
        $symbols->code = $mould_code_symbols;
        $data = array(
            'condition_1' => array(
                'table' => 'mould',
                'fields' => ['code', 'chinese_name'],
                'where' => $whereAttr,
                'limit' => ["ALL"],
                'symbols' => $symbols
            )
        );
        $mould = CommonSqlSyntax_Query($data, "MsSQL", "mould");
        if ($mould['Response'] !== 'ok') {
            return $mould;
        } else if (count($mould['QueryTableData']) == 0) {
            $mould['Response'] = "no data";
            // return $mould;
        }
        $mould_data = $mould['QueryTableData'];
    } else {
        $mould_data = [];
    }

    //查詢wire_scroll_no_use
    $symbols = new stdClass();
    $symbols->work_code = ["equal"];
    $whereAttr = new stdClass();
    $whereAttr->work_code = [$workID];//輸入的工單編號
    $orderby = ['asc', 'upload_at'];
    $data = array(
        'condition_1' => array(
            'table' => 'wire_scroll_no_use',
            'where' => $whereAttr,
            'limit' => ["ALL"],
            'orderby' => ['asc', 'upload_at'],
            'symbols' => $symbols
        )
    );
    $wire_scroll_no_use = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    if ($wire_scroll_no_use['Response'] !== 'ok') {
        return $wire_scroll_no_use;
    } else if (count($wire_scroll_no_use['QueryTableData']) == 0) {
        // $wire_scroll_no_use['Response'] = "no data";
        // return $wire_scroll_no_use;
    }
    $wire_scroll_no_use_data = $wire_scroll_no_use['QueryTableData'];

    $query_furnace_code = [];
    $query_furnace_code_symbols = [];
    foreach ($wire_scroll_no_use_data as $key => $value) {
        if (!in_array($value['scroll_no'], $query_furnace_code)) {
            array_push($query_furnace_code, $value['scroll_no']);
            array_push($query_furnace_code_symbols, "equal");
        }
    }
    
    //查詢wire_stack
    if (!empty($query_furnace_code)) {
        $whereAttr = new stdClass();
        $whereAttr->scroll_no = $query_furnace_code;
        $symbols = new stdClass();
        $symbols->scroll_no = $query_furnace_code_symbols;
        $data = array(
            'condition_1' => array(
                'table' => 'wire_stack',
                'fields' => ['scroll_no', 'furnace_code'],
                'where' => $whereAttr,
                'symbols' => $symbols
            )
        );
        $wire_stack = CommonSqlSyntax_Query($data, "MsSQL");
        if ($wire_stack['Response'] !== 'ok') {
            return $wire_stack;
        } else if (count($wire_stack['QueryTableData']) == 0) {
            $wire_stack['Response'] = "no data";
            return $wire_stack;
        }
        $wire_stack_data = $wire_stack['QueryTableData'];
    } else {
        $wire_stack_data = [];
    }

    //查詢inspection
    $symbols = new stdClass();
    $symbols->work_code = ["equal"];
    $whereAttr = new stdClass();
    $whereAttr->work_code = [$workID];
    $orderby = ['desc', 'upload_at'];
    $data = array(
        'condition_1' => array(
            'table' => 'inspection',
            'where' => $whereAttr,
            'orderby' => $orderby,
            'symbols' => $symbols
        )
    );
    $inspection = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
    if ($inspection['Response'] !== 'ok') {
        return $inspection;
    } else if (count($inspection['QueryTableData']) == 0) {
        // $inspection['Response'] = "no data";
        // return $inspection;
    }
    $inspection_data = $inspection['QueryTableData'];

    // //查詢製程的名稱與該製程的檢驗項目的名稱與值
    // $fields = new stdClass();
    // $fields->project = ["id", "name"];
    // $fields->check = ['code','chinese_name','english_name'];
    // $fields->category = ['code','name'];
    // $fields->commodity_specification = ["value"];
    // $join = new stdClass();
    // $join->commodity = [];
    // $commodity_specification = new stdClass();
    // $commodity_specification->commodity_specification = new stdClass();
    // $commodity_specification->commodity_specification->id = new stdClass();
    // $commodity_specification->commodity_specification->id = "commodity_id";
    // $commodity_specification->commodity_specification->JOIN = new stdClass();
    // $commodity_specification->commodity_specification->JOIN->project = new stdClass();
    // $commodity_specification->commodity_specification->JOIN->project->project_id = new stdClass();
    // $commodity_specification->commodity_specification->JOIN->project->project_id = "id";
    // $commodity_specification->commodity_specification->JOIN->category = new stdClass();
    // $commodity_specification->commodity_specification->JOIN->category->category_id = new stdClass();
    // $commodity_specification->commodity_specification->JOIN->category->category_id = "id";
    // $commodity_specification->commodity_specification->JOIN->check = new stdClass();
    // $commodity_specification->commodity_specification->JOIN->check->check_id = new stdClass();
    // $commodity_specification->commodity_specification->JOIN->check->check_id = "id";
    // array_push($join->commodity, $commodity_specification);
    // $tables = ['commodity', 'commodity_specification', 'project', 'category', 'check'];
    // $whereAttr = new stdClass();
    // $whereAttr->commodity = new stdClass();
    // $whereAttr->commodity->code = [$workorder_related_data[0]['work_order$commodity_code']];//輸入的工單編號
    // $whereAttr->project = new stdClass();
    // $whereAttr->project->id = $project_array;//查詢現有的製程
    // $symbols = new stdClass();
    // $symbols->commodity = new stdClass();
    // $symbols->commodity->code = ['equal'];//輸入的工單編號
    // $symbols->project = new stdClass();
    // $symbols->project->id = [];
    // $i = 0;
    // while ($i < count($project_array)) {
    //     array_push($symbols->project->id, 'equal');
    //     $i++;
    // }
    // $jointype = new stdClass();
    // $jointype->commodity_commodity_specification= "inner";
    // $jointype->commodity_specification_project= "inner";
    // $jointype->commodity_specification_category= "inner";
    // $jointype->commodity_specification_check= "inner";
    // $data = array(
    //     'condition_1' => array(
    //         'fields' => $fields,
    //         'join' => $join,
    //         'jointype' => $jointype,
    //         'tables' => $tables,
    //         'where' => $whereAttr,
    //         'symbols' => $symbols
    //     )
    // );
    // $project = CommonSqlSyntaxJoin_Query($data, "MsSQL");
    // if ($project['Response'] !== 'ok') {
    //     return $project;
    // } else if (count($project['QueryTableData']) == 0) {
    //     $project['Response'] = "no data";
    //     return $project;
    // }
    // $process_name = $project['QueryTableData'];

    // $process_name = [];//製程名稱
    // $process_check = [];//製程與對應的檢驗項目
    // for ($i=0; $i < count($process_name); $i++) { 
    //     //製程名稱
    //     $process_name += array(
    //         $process_name[$i]['project$id'] => $process_name[$i]['project$name']
    //     );

    //     //製程與對應的檢驗項目
    //     $this_process_check = array(
    //         $process_name[$i]['check$code'] => array(
    //             'chinese_name' => $process_name[$i]['check$chinese_name'],
    //             'standard' => $process_name[$i]['category$code'],
    //             'standardValue' => $process_name[$i]['commodity_specification$value']
    //         ) 
    //     );
    //     if (!array_key_exists($process_name[$i]['project$id'], $process_check)) {
    //         $process_check += array(
    //             $process_name[$i]['project$id'] => $this_process_check
    //         );
    //     } else {
    //         $process_check[$process_name[$i]['project$id']] += $this_process_check;
    //     }
    // };

    $process_name = [];//製程名稱
    $process_check = [];//製程與對應的檢驗項目
    if (!empty($workorder_related_data)) {
        if (is_string($workorder_related_data[0]['v_cd_sp$op_json'])) {
            $op_json = json_decode($workorder_related_data[0]['v_cd_sp$op_json'], true);
        } else {
            $op_json = $workorder_related_data[0]['v_cd_sp$op_json'];
        }
        
        foreach ($op_json as $process => $insp_data) {
            //製程代號
            $this_process = 0;
            //製程與對應的檢驗項目
            if ($process == '打頭') {
                $process_name += array(
                    '5' => $process
                );
                $this_process = 5;
            } else if ($process == '輾牙') {
                $process_name += array(
                    '6' => $process
                );
                $this_process = 6;
            } else  if ($process == '熱處理') {
                $process_name += array(
                    '7' => $process
                );
                $this_process = 7;
            }
            
            for ($i=0; $i < count($insp_data); $i++) { 
                $this_process_check = array(
                    $insp_data[$i]['檢驗代碼'] => array(
                        'chinese_name' => $insp_data[$i]['檢驗名稱'],
                        'standard' => $insp_data[$i]['檢驗方式'],
                        'standardValue' => $insp_data[$i]['檢驗值']
                    ) 
                );
                if (!array_key_exists($this_process, $process_check)) {
                    $process_check += array(
                        $this_process => $this_process_check
                    );
                } else {
                    $process_check[$this_process] += $this_process_check;
                }
            }
        }
    }

    //查詢runcard
    $symbols = new stdClass();
    $symbols->runcard_code = ["like"];
    $whereAttr = new stdClass();
    $whereAttr->runcard_code = [$workID];//輸入的工單編號
    $data = array(
        'condition_1' => array(
            'table' => 'runcard',
            'where' => $whereAttr,
            'symbols' => $symbols
        )
    );
    $runcard = CommonSqlSyntax_Query($data, "PostgreSQL", "runcard");
    if ($runcard['Response'] !== 'ok') {
        return $runcard;
    } else if (count($runcard['QueryTableData']) == 0) {
        // $runcard['Response'] = "no data";
        // return $runcard;
    }
    $runcard_data = $runcard['QueryTableData'];

    //該工單相關資料
    if (!empty($workorder_related_data)) {
        $unit_weight = $workorder_related_data[0]['v_cd_sp$standard_weight'];
        $material_weight = $workorder_related_data[0]['v_cd_sp$plum_weight'] > 0 ? $workorder_related_data[0]['v_cd_sp$standard_weight'] + $workorder_related_data[0]['v_cd_sp$plum_weight'] : $workorder_related_data[0]['v_cd_sp$standard_weight'] * 1.15;
        $workorder_detail[0] = array(
            'workCode' => $workorder_related_data[0]['work_order$code'],
            'workOrgCode' => $workorder_related_data[0]['work_order$org_code'],
            'work_qty' => $workorder_related_data[0]['work_order$work_qty'],
            'commodity_code' => $workorder_related_data[0]['work_order$commodity_code'],
            'unit_weight' => $unit_weight,
            'standard_weight' => round($unit_weight * $workorder_related_data[0]['work_order$work_qty'] / 1000, 2),
            'product_name' => $workorder_related_data[0]['v_cd_sp$cd_name'],
            'wire_commodity_code' => $workorder_related_data[0]['work_order$wire_code'],
            'wire_product_name' => $workorder_related_data[0]['wire_box$chinese_name'],
            'material_weight' => $material_weight,
            'wire_need_weight' => round($material_weight * $workorder_related_data[0]['work_order$work_qty'] / 1000, 2),
            'mould_code' => $workorder_related_data[0]['work_order$mould_code'],
            'control_card' => $workorder_related_data[0]['work_order$control_card'],
            'total_expend' => 0,
            'loss_rate' => 0,
            'total_work_time' => '-',
        );
    } else {
        $workorder_detail[0] = array(
            'workCode' => $workID,
            'workOrgCode' => '-',
            'work_qty' => '-',
            'commodity_code' => '-',
            'unit_weight' => 0,
            'standard_weight' => 0,
            'product_name' => '-',
            'wire_commodity_code' => '-',
            'wire_product_name' => '-',
            'material_weight' => 0,
            'wire_need_weight' => 0,
            'mould_code' => '-',
            'control_card' => '-',
            'total_expend' => 0,
            'loss_rate' => 0,
            'total_work_time' => '-'
        );
    }
    
    //線材使用資訊表格
    $wireData = [];
    $scroll_no = [];
    for ($i=0; $i < count($wire_scroll_no_use_data); $i++) { 
        if (!in_array($wire_scroll_no_use_data[$i]['work_code'], $scroll_no)) {
            array_push($scroll_no, $wire_scroll_no_use_data[$i]['work_code']);
            array_push($wireData, $wire_scroll_no_use_data[$i]);
        } else {
            $wirePosition = array_search($wire_scroll_no_use_data[$i]['work_code'], $scroll_no, true);
            if ($wireData[$wirePosition]['status'] == 'S' && $wire_scroll_no_use_data[$i]['status'] == 'E') {
                $wireData[$wirePosition]['weight'] = $wireData[$wirePosition]['weight'] - $wire_scroll_no_use_data[$i]['weight'];
                $wireData[$wirePosition]['status'] = 'E';
                $wireData[$wirePosition]['pair'] = 1;
            } else if ($wireData[$wirePosition]['status'] = 'E') {
                if (isset($wireData[$wirePosition]['pair'])){
                    array_unshift($scroll_no, $wire_scroll_no_use_data[$i]['work_code']);
                    array_unshift($wireData, $wire_scroll_no_use_data[$i]);
                } else {
                    $wireData[$wirePosition]['weight'] = $wire_scroll_no_use_data[$i]['weight'] - $wireData[$wirePosition]['weight'];
                    $wireData[$wirePosition]['status'] = 'E';
                    $wireData[$wirePosition]['pair'] = 1;
                }
            }
        }
    }
    $wire_information = [];
    for ($i=0; $i < count($wireData); $i++) { 
        $this_furnaceCode = '-';
        for ($j=0; $j < count($wire_stack_data); $j++) { 
            if ($wireData[$i]['scroll_no'] == $wire_stack_data[$j]['scroll_no']) {
                $this_furnaceCode = $wire_stack_data[$j]['furnace_code'];
            }
        }
        if (isset($wireData[$i]['pair'])) {
            $wire_information[$i] = array(
                'code' => $wireData[$i]['scroll_no'],
                'furnaceCode' => $this_furnaceCode,
                'consumption' => $wireData[$i]['weight'] < 0 ? '-' : $wireData[$i]['weight']
            );
        }
        // else {
        //     $wire_information[$i] = array(
        //         'code' => $wireData[$i]['scroll_no'],
        //         'furnaceCode' => $wireData[$i]['furnace_code'],
        //         'consumption' => '上線中'
        //     );
        // }
    }

    //生產重量資訊表格
    $production_weight = [];
    for ($i=0; $i < count($runcard_data); $i++) { 
        if (in_array($runcard_data[$i]['project_id'], array_column($production_weight, 'code'))) {
            $production_weight[array_search($runcard_data[$i]['project_id'], array_column($production_weight, 'code'))]['totalBucketWeight'] += $runcard_data[$i]['screw_weight'];
        } else {
            $production_weight[count($production_weight)] = array(
                'code' => $runcard_data[$i]['project_id'],
                'unit_weight' => 0,
                'totalBucketWeight' => $runcard_data[$i]['screw_weight'],
                'consumption_rate' => '-',
            );
        }
    }
    for ($i=0; $i < count($production_weight); $i++) { 
        if ($workorder_detail[0]['work_qty'] != 0 && $workorder_detail[0]['work_qty'] != '-') {
            $production_weight[$i]['unit_weight'] =  round($production_weight[$i]['totalBucketWeight'] / $workorder_detail[0]['work_qty'], 3);
        } else {
            $production_weight[$i]['unit_weight'] = '-';
        }
        if (!empty($process_name[$production_weight[$i]['code']])) {
            $production_weight[$i]['code'] = $process_name[$production_weight[$i]['code']];
        } else {
            $production_weight[$i]['code'] = '-';
        }
    }

    //使用模具表格
    $use_mold = [];
    for ($i=0; $i < count($mould_series_no_use_data); $i++) {
        for ($j=0; $j < count($mould_data); $j++) { 
            if ($mould_series_no_use_data[$i]['mould_code'] == $mould_data[$j]['code']) {
                $use_mold[$i] = array(
                    'code' => $mould_series_no_use_data[$i]['mould_code'],
                    'seriesNo' => $mould_series_no_use_data[$i]['mould_series_no'],
                    'name' => $mould_data[$j]['chinese_name'],
                );
            }
        } 
    }

    //使用牙板表格
    $use_thread = [];
    for ($i=0; $i < count($thread_series_no_use_data); $i++) {
        for ($j=0; $j < count($mould_data); $j++) { 
            if ($thread_series_no_use_data[$i]['thread_code'] == $mould_data[$j]['code']) {
                $use_thread[$i] = array(
                    'code' => $thread_series_no_use_data[$i]['thread_code'],
                    'seriesNo' => $thread_series_no_use_data[$i]['thread_series_no'],
                    'name' => $mould_data[$j]['chinese_name'],
                );
            }
        } 
    }

    // //使用耗材表格
    // $use_material = [];
    // for ($i=0; $i < count($material_batch_no_use_data); $i++) {
    //     if (in_array($material_batch_no_use_data[$i]['materia_code'], array_column($use_material, 'code'))) {
    //         $use_material[array_search($material_batch_no_use_data[$i]['materia_code'], array_column($use_material, 'code'))]['use_qty']++;
    //     } else {
    //         for ($j=0; $j < count($mould_data); $j++) { 
    //             if ($material_batch_no_use_data[$i]['materia_code'] == $mould_data[$j]['code']) {
    //                 $use_material[count($use_material)] = array(
    //                     'code' => $material_batch_no_use_data[$i]['materia_code'],
    //                     'use_qty' => 1,
    //                     'name' => $mould_data[$j]['chinese_name'],
    //                 );
    //             }
    //         } 
    //     }
    //     // if (in_array($material_batch_no_use_data[$i]['material_code'], array_column($use_material, 'code'))) {
    //     //     $use_material[array_search($material_batch_no_use_data[$i]['material_code'], array_column($use_material, 'code'))]['use_qty']++;
    //     // } else {
    //     //     for ($j=0; $j < count($mould_data); $j++) { 
    //     //         if ($material_batch_no_use_data[$i]['material_code'] == $mould_data[$j]['code']) {
    //     //             $use_material[count($use_material)]] = array(
    //     //                 'code' => $material_batch_no_use_data[$i]['material_code'],
    //     //                 'use_qty' => 1,
    //     //                 'name' => $mould_data[$j]['chinese_name'],
    //     //             );
    //     //         }
    //     //     } 
    //     // }
    // }

    //標準單支重
    $standard_weight = $workorder_detail[0]['unit_weight'];
    if (!is_numeric($standard_weight)) {
        $standard_weight = 0;
    }
    //檢驗數據表格
    //檢驗單支重
    $inspection_data_length = count($inspection_data);
    $inspection_total = 0;
    $inspection_count = 0;
    $inspection_actual_weight = 0;
    $total_inspection_data = [];//記錄所有製程的檢驗紀錄
    for ($i=0; $i < $inspection_data_length; $i++) {
        if (is_string($inspection_data[$i]['inspection_detail'])) {
            $inspection_detail = json_decode($inspection_data[$i]['inspection_detail'], true);
        } else {
            $inspection_detail = $inspection_data[$i]['inspection_detail'];
        }

        //輾牙沒有重量
        if (!empty($inspection_detail['act_wgt'])) {
            $inspection_total += floatval($inspection_detail['act_wgt']);
            $inspection_count++;
        }

        $this_inspection = [];//紀錄該筆檢驗資料
        foreach ($process_check[$inspection_data[$i]['project_id']] as $check_code => $value) {
            $standardValue = "";
            if ($value['standard'] == 'BETWEEN') {
                $this_process_check_standard_value = explode("~",$value['standardValue']);

                $standardValue = $this_process_check_standard_value[0] . '~' . $this_process_check_standard_value[1];
            } else if ($value['standard'] == 'MIN') {
                $standardValue = '≧' . $value['standardValue'];
            } else if ($value['standard'] == 'MAX') {
                $standardValue = '≦' . $value['standardValue'];
            } else if ($value['standard'] == 'TOOL') {
                $standardValue = $value['standardValue'];
            }

            if (isset($inspection_detail[$check_code])) {
                array_push($this_inspection, array(
                    'code' => $value['chinese_name'],
                    'standardValue' => $standardValue,
                    'inspectionValue' => $inspection_detail[$check_code]['value'],
                    'result' => $inspection_detail[$check_code]['result']==1?'PASS':'NG'
                ));
            } else {
                array_push($this_inspection, array(
                    'code' => $value['chinese_name'],
                    'standardValue' => $standardValue,
                    'inspectionValue' => '--',
                    'result' => '--'
                ));
            }
        }

        //檢驗單支重
        if (isset($inspection_detail['act_wgt'])) {
            $unit_weight = floatval($inspection_detail['act_wgt']);
            if ($unit_weight != 0) {
                $unit_range = [$standard_weight * 0.9, $standard_weight * 1.1];

                if ($unit_range[0] <= $unit_weight && $unit_weight <= $unit_range[1]) {
                    $unit_result = 'PASS';
                } else {
                    $unit_result = 'NG';
                }
                array_push($this_inspection, array(
                    'code' => '單支重',
                    'standardValue' => $unit_range[0] . '~' . $unit_range[1],
                    'inspectionValue' => $unit_weight,
                    'result' => $unit_result
                ));
            } else {
                array_push($this_inspection, array(
                    'code' => '單支重',
                    'standardValue' => '--',
                    'inspectionValue' => 0,
                    'result' => '--'
                ));
            }
        }
        
        //將各筆檢驗資料儲存並以製程分類
        if (!array_key_exists($inspection_data[$i]['project_id'], $total_inspection_data)) {
            $total_inspection_data += array(
                $inspection_data[$i]['project_id'] => []
            );
        }
        array_push($total_inspection_data[$inspection_data[$i]['project_id']], array(
            'inspection' => $this_inspection,
            'timestamp' =>$inspection_data[$i]['upload_at']
        ));
    }

    if ($inspection_count != 0) {
        //平均單筆單支重=實際單支重
        $inspection_actual_weight = round($inspection_total / $inspection_count, 2);
        if ($inspection_actual_weight > 0) {
            $workorder_detail[0]['actual_weight'] = $inspection_actual_weight;
        } else {
            $workorder_detail[0]['actual_weight'] = 0;
        }
    }

    //總生產時間表格
    $total_work_time = [];
    for ($i=0; $i < count($work_code_use_data); $i++) { 
        if (in_array($work_code_use_data[$i]['project_id'], array_column($total_work_time, 'code'))) {
            $work_code_use_dataPosition = array_search($work_code_use_data[$i]['project_id'], array_column($total_work_time, 'code'));
            if ($work_code_use_data[$i]['status'] == 'S') {
                if ($total_work_time[$work_code_use_dataPosition]['startTime'] == '-') {
                    $total_work_time[$work_code_use_dataPosition]['startTime'] = $work_code_use_data[$i]['upload_at'];
                } else {
                    if (strtotime($total_work_time[$work_code_use_dataPosition]['startTime']) > strtotime($work_code_use_data[$i]['upload_at'])) {
                        $total_work_time[$work_code_use_dataPosition]['startTime'] = $work_code_use_data[$i]['upload_at'];
                    }
                }
            } else if ($work_code_use_data[$i]['status'] == 'E') {
                if ($total_work_time[$work_code_use_dataPosition]['endTime'] == '-') {
                    $total_work_time[$work_code_use_dataPosition]['endTime'] = $work_code_use_data[$i]['upload_at'];
                } else {
                    if (strtotime($work_code_use_data[$i]['upload_at']) > strtotime($total_work_time[$work_code_use_dataPosition]['endTime'])) {
                        $total_work_time[$work_code_use_dataPosition]['endTime'] = $work_code_use_data[$i]['upload_at'];
                    }
                }
            }
        } else {
            if ($work_code_use_data[$i]['status'] == 'S') {
                $total_work_time[count($total_work_time)] = array(
                    'code' => $work_code_use_data[$i]['project_id'],
                    'device_name' => $work_code_use_data[$i]['device_name'],
                    'startTime' => $work_code_use_data[$i]['upload_at'],
                    'endTime' => '-',
                    'totalTime' => '-',
                );
            } else if ($work_code_use_data[$i]['status'] == 'E') {
                $total_work_time[count($total_work_time)] = array(
                    'code' => $work_code_use_data[$i]['project_id'],
                    'device_name' => $work_code_use_data[$i]['device_name'],
                    'startTime' => '-',
                    'endTime' => $work_code_use_data[$i]['upload_at'],
                    'totalTime' => '-',
                );
            }
        }
    }
    for ($i=0; $i < count($total_work_time); $i++) { 
        $projectWorkRunTime = TimeSubtraction($total_work_time[$i]['startTime'], $total_work_time[$i]['endTime'], 'hour');
        if (!empty($process_name[$total_work_time[$i]['code']])) {
            $total_work_time[$i]['code'] = $process_name[$total_work_time[$i]['code']];
        } else {
            $total_work_time[$i]['code'] = '-';
        }
        $total_work_time[$i]['totalTime'] = $projectWorkRunTime[0];
    }

    //將沒有檢測資料的製程清除
    foreach ($process_name as $process_id => $process_value) {
        if (empty($total_inspection_data[$process_id])) {
            unset($process_name[$process_id]);
        }
    }

    //計算總耗用量與損耗率
    $total_expend = 0;
    for ($i=0; $i < count($wire_information); $i++) {
        if (is_string($wire_information[$i]['consumption'])) {
        break;
        } 
        $total_expend += $wire_information[$i]['consumption'];
    }
    $workorder_detail[0]['total_expend'] = $total_expend;
    //若等於0會出錯
    if ($total_expend != 0) {
        $loss_rate = round((($total_expend - $workorder_detail[0]['wire_need_weight']) / $total_expend) * 100, 2);
        if ($loss_rate < 0) {
            $workorder_detail[0]['loss_rate'] = 0;
        } else {
            $workorder_detail[0]['loss_rate'] = $loss_rate;
        }
    }

    //計算總生產時間
    if (!empty($total_work_time)) {
        $totalWorkRunTime = TimeSubtraction($total_work_time[0]['startTime'], $total_work_time[count($total_work_time) - 1]['endTime'], 'date');
        $workorder_detail[0]['total_work_time'] = $totalWorkRunTime[1] . '(' . $total_work_time[0]['startTime'] . ' ~ ' . $total_work_time[count($total_work_time) - 1]['endTime'] . ')';
    }

    $returnData['Response'] = 'ok';
    $returnData['QueryTableData'] = [];
    $returnData['QueryTableData'][0] = array(
        'workorder_detail' => $workorder_detail,
        'wire_information' => $wire_information,
        'production_weight' => $production_weight,
        'use_mold' => $use_mold,
        'use_thread' => $use_thread,
        // 'use_material' => $use_material,
        'project_data' => $process_name,
        'total_inspection_data' => $total_inspection_data,
        'total_work_time' => $total_work_time
    );
    return $returnData;
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

//警報履歷
function AlarmHistory($params){
    // $start_date_time = date("Y-m-d 08:00:00", strtotime($params->startTime));
    // $end_date_time = date("Y-m-d 08:00:00", strtotime($params->endTime));
    $device_name = $params->otherData;
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

    $time_interval = array(
        'start' => $start_date_time,
        'end' => $end_date_time
    );

    if (isset($device_name)) {
        $symbols = new stdClass();
        $symbols->name = ['equal'];
        $whereAttr = new stdClass();
        $whereAttr->name = [$device_name];
    }
    $data = array(
        'condition_1' => array(
            'table' => 'device_box',
            'where' => isset($whereAttr)?$whereAttr:'',
            'limit' => ['ALL'],
            'symbols' => isset($symbols)?$symbols:''
        )
    );
    $device_box = CommonSqlSyntax_Query($data, "MsSQL");
    if ($device_box['Response'] !== 'ok') {
        return $device_box;
    } else if (count($device_box['QueryTableData']) == 0) {
        $returnData['Response'] = 'no device data';
        return $returnData;
    }

    if (!empty($device_box)) {
        $device_box_data = $device_box['QueryTableData'];
        if ($device_box_data[0]['note'] == '打頭機') {
            $process = 5;
        } else if ($device_box_data[0]['note'] == '輾牙機') {
            $process = 6;
        }
    }

    if (isset($device_name)) {
        $symbols = new stdClass();
        $symbols->device_name = ['equal'];
        $whereAttr = new stdClass();
        $whereAttr->device_name = [$device_name];
    }
    $data = array(
        'condition_1' => array(
            'intervaltime' => array('upload_at' => array(array($time_interval['start'], $time_interval['end']))),
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
        // $returnData['Response'] = 'no data';
        // return $returnData;
    }
    $Query_Device_Response = $machine_status_sum['QueryTableData'];
    //若當資料重疊，則修改查詢開關機時間的時間
    if (date("Y-m-d", strtotime($params->startTime)) == date("Y-m-d", strtotime($params->endTime)) && date("Y-m-d", strtotime($params->startTime)) == date("Y-m-d")) {
        [$machine_on_off_hist_data, $machine_on_off_hist_SQL] = machine_on_off_hist($device_name, array('start'=>date("Y-m-d 08:00:00"), 'end'=>date("Y-m-d H:i:s")));
    } else {
        [$machine_on_off_hist_data, $machine_on_off_hist_SQL] = machine_on_off_hist($device_name, $time_interval);
    }
    $machine_abn_data = machine_abn();

    if ($query_now_status == true) {
        //查詢機台機型
        $machine_model_data = Query_machine_model([array('device_name'=>$device_name)]);
        
        //查詢機型燈號
        $machine_light_data = Query_machine_light($machine_model_data);

        //取得該機台的燈號異常值
        $machine_light_abn_data = Query_machine_light_abn($machine_light_data, $machine_abn_data);

        [$Query_Device_data, $device_out_put_data] = Query_Device(date("Y-m-d 08:00:00"), $now_date_time, $device_name, $machine_on_off_hist_data, $machine_light_abn_data[$device_name], $process);
        for ($i=0; $i < count($Query_Device_data); $i++) { 
            $Query_Device_data[$i]['upload_at'] = date("Y-m-d", strtotime($now_date_time)+86400);
            array_push($Query_Device_Response, $Query_Device_data[$i]);
        }
    }

    if (empty($Query_Device_Response)) {
        $returnData['Response'] = 'no data';
        return $returnData;
    }

    $abn_species = array(
        'data' => [],
        'data_time' => []   
    );
    $device_detail_data = array();
    $err_time = array();
    foreach ($Query_Device_Response as $key => $status_value) {
        $this_data_time = date("Y-m-d", strtotime($status_value['upload_at'])-86400);
        $this_data_time = explode("-", $this_data_time);
        if (!in_array($this_data_time[0] . '年' . $this_data_time[1] . '月', $abn_species['data_time'])) {
            array_push($abn_species['data_time'], $this_data_time[0] . '年' . $this_data_time[1] . '月');
        }

        $position = array_search($this_data_time[0] . '年' . $this_data_time[1] . '月', $abn_species['data_time']);

        foreach ($status_value['machine_detail']['H']['datail'] as $err_key => $err_value) {
            foreach ($err_value['machine_abn_description'] as $abn_description_key => $abn_description_value) {
                if (!isset($abn_species['data'][$abn_description_value])) {
                    $abn_species['data'][$abn_description_value] = array('data' => []);
                }
                if (!isset($abn_species['data'][$abn_description_value]['data'][$position])) {
                    $abn_species['data'][$abn_description_value]['data'][$position] = 0;
                }
                $abn_species['data'][$abn_description_value]['data'][$position]++;
            }

            $durationTime = TimeSubtraction($err_value['timestamp'][0], $err_value['timestamp'][1], 'hour');

            $err_startTime = date("Y-m-d H:i:s",strtotime($err_value['timestamp'][0]));
            $err_endTime = date("Y-m-d H:i:s",strtotime($err_value['timestamp'][1]));
            array_push($err_time, array($err_startTime, $err_endTime));
            array_push($device_detail_data, array(
                'alarmCode' => implode("\n", $err_value['machine_abn_id']),
                'alarmDetail' => implode("\n", $err_value['machine_abn_description']),
                'alarmVideo' => '',
                'startTime' => $err_startTime,
                'endTime' => $err_endTime,
                'continuousTime' => $durationTime[0]
            ));
        }
    }

    if (!empty($err_time)) {
        $whereAttr = new stdClass();
        $whereAttr->device_name = [$device_name];
        $symbols = new stdClass();
        $symbols->device_name = ['equal'];
        $data = array(
            'condition_1' => array(
                'intervaltime' => array('alarm_time' => $err_time),
                'table' => 'machine_alarm_video',
                'where' => isset($whereAttr)?$whereAttr:'',
                'limit' => ['ALL'],
                'symbols' => isset($symbols)?$symbols:''
            )
        );
        $machine_alarm_video = CommonSqlSyntax_Query_v2_5($data, "PostgreSQL");
        if ($machine_alarm_video['Response'] !== 'ok') {
            return [[],[]];
        } else if (count($machine_alarm_video['QueryTableData']) == 0) {
            // return [[],[]];
        }
        $machine_alarm_video = $machine_alarm_video['QueryTableData'];
    }

    if (count($device_detail_data) == 0) {
        $returnData['Response'] = '當日無異常資料';
        return  $returnData;
    } else {
        if (isset($machine_alarm_video)) {
            foreach ($machine_alarm_video as $alarm_video_key => $alarm_video_value) {
                if (in_array(substr($alarm_video_value['alarm_time'], 0, 19), array_column($device_detail_data, 'startTime'))) {
                    $device_detail_dataPosition = array_search(substr($alarm_video_value['alarm_time'], 0, 19), array_column($device_detail_data, 'startTime'));
                    $device_detail_data[$device_detail_dataPosition]['alarmVideo'] = $alarm_video_value['video_name'];
                }
            }
        }
    }
    $returnData['QueryTableData'][0]['abn_species'] = $abn_species;
    $returnData['QueryTableData'][0]['device_detail_data'] = $device_detail_data;
    $returnData['QueryTableData'][0]['query_date'] = [$params->startTime, $params->endTime];
    $returnData['Response'] = 'ok';
    return  $returnData;
}

function QueryMachineCamera($params){
    $device_name = $params->device_name;
    $data = array(
        'col' => 'device_name',
        'valueStart' => $device_name,
        'valueEnd' => $device_name
    );
    $machine_camera = CommonIntervalQuery($data, 'MySQL', 'machine_camera');
    if ($machine_camera['Response'] !== 'ok') {
        $returnData['Response'] = 'erro';
        $returnData['QueryTableData'] = $machine_camera;
        return $returnData;
    }
    $machine_camera_data = $machine_camera['QueryTableData'];
    
    $returnData = array();
    $returnData['Response'] = 'ok';
    $returnData['QueryTableData'] = $machine_camera_data;

    return $returnData;
}

function QueryMachineStatusList($params){
    $device_model = $params->device_model;
    $data = array(
        'col' => 'model',
        'valueStart' => $device_model,
        'valueEnd' => $device_model
    );
    $machine_status_list = CommonIntervalQuery($data, 'MySQL', 'machine_status_list');
    if ($machine_status_list['Response'] !== 'ok') {
        $returnData['Response'] = 'erro';
        $returnData['QueryTableData'] = $machine_status_list;
        return $returnData;
    }
    $machine_status_list_data = $machine_status_list['QueryTableData'];
    
    $returnData = array();
    $returnData['Response'] = 'ok';
    $returnData['QueryTableData'] = $machine_status_list_data;

    return $returnData;
}


//demo用計數器
function DemoCounter($params){
    $device_name = $params->deviceID;
    $process = $params->process;
    $previous_time = date("Y-m-d 08:00:00");
    $now_time = date("Y-m-d H:i:s");
    if (strtotime($now_time) < strtotime($previous_time)) {
        $previous_time = date("Y-m-d H:i:s", strtotime($previous_time)-86400);
    }
    //查詢單一機台當日資料
    $device_data = Query_Device_Data($device_name, $previous_time, $now_time);

    //將$device_data內的JSON字串轉為Object
    foreach ($device_data as $key => $value) {
        if (is_string($value['machine_detail'])) {
            $machine_detail = json_decode($value['machine_detail'], true);
            $device_data[$key]['machine_detail'] = $machine_detail;
        }
    }

    if ($process == '打頭') {
        $this_process = 5;
    } else if ($process == '輾牙') {
        $this_process = 6;
    }

    if ($this_process == 5) {
        //取得機台目前支數
        $device_now_count = Get_Device_Now_Count($device_data);
    } else if ($this_process == 6) {
        //查詢輾牙暫存表
        [$machine_status_data, $machine_status_thd_SQL] = machine_status_thd($device_name);

        //機台詳細資料
        if (is_string($machine_status_data[0]['machine_detail'])) {
            $machine_status_data[0]['machine_detail'] = json_decode($machine_status_data[0]['machine_detail'], true);
        }

        if (isset($machine_status_data[0]['machine_detail']['cnt'])) {
            //機台支數
            $device_count = $machine_status_data[0]['machine_detail']['cnt'];
        } else {
            $device_count = null;
        }

        //確認有工單
        if ($machine_status_data[0]['work_code'] != "") {
            [$work_code_use_data, $work_code_use_SQL] = work_code_use($device_name, $machine_status_data[0]['work_code'], $this_process);
        }

        //取得工單開始時間
        $wrok_code_start_time = '';
        if (isset($work_code_use_data)) {
            foreach ($work_code_use_data as $key => $value) {
                if ($value['status'] == 'S') {
                    !empty($wrok_code_start_time) ? (strtotime($value['upload_at']) > strtotime($wrok_code_start_time) ? $wrok_code_start_time = $value['upload_at'] : '') : $wrok_code_start_time = $value['upload_at'];
                }
            }
        }
        $device_now_count = get_start_count($device_name, $wrok_code_start_time, $device_count);
    }

    //整理取得該機台當日支數資料
    $device_out_put_data = Get_Device_Out_Put($device_data);

    $returnData['Response'] = 'ok';
    $returnData['page'] = 'machstatus';
    $returnData['QueryTableData'] = [];

    array_push($returnData['QueryTableData'], array(
        'device_count' => isset($device_now_count) ? $device_now_count : '--',
        'device_cumulative_production' => isset($device_out_put_data) ? $device_out_put_data : '--'
    ));
    return $returnData;
}