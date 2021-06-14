<?php
function MainQuery($params)//主要查詢按鈕
{
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
        // 'deviceID' => array('device_box', 'name'),
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
    // $jointype->work_order_device_box= "inner";
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
                        // 'factory_name' => '二廠',
                        // 'group_name' => '成四組',
                        // 'device_name' => $workorder_related_data[$i]['device_box$name'],
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
            //         // 'factory_name' => '二廠',
            //         // 'group_name' => '成四組',
            //         // 'device_name' => $workorder_related_data[$i]['device_box$name'],
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

function QueryWorkId($params)//主要查詢按鈕
{
    $workID = $params->workID;

    //join work_order,commodity,device_box,wire_box
    $fields = new stdClass();
    $fields->work_order = ["code", "status", "org_code", "work_qty", "wire_code", "control_card", "commodity_code", "mould_code", "source_wgt"];
    $fields->v_cd_sp = "";
    $fields->device_box = ["name"];
    $fields->wire_box = ["chinese_name"];
    $join = new stdClass();
    $join->work_order = [];
    $device_box = new stdClass();
    $device_box->device_box = new stdClass();
    $device_box->device_box->device_name = new stdClass();
    $device_box->device_box->device_name = "name";
    $v_cd_sp = new stdClass();
    $v_cd_sp->v_cd_sp = new stdClass();
    $v_cd_sp->v_cd_sp->commodity_code = new stdClass();
    $v_cd_sp->v_cd_sp->commodity_code = "org_code";
    $wire_box = new stdClass();
    $wire_box->wire_box = new stdClass();
    $wire_box->wire_box->wire_code = new stdClass();
    $wire_box->wire_box->wire_code = "code";
    array_push($join->work_order, $device_box);
    array_push($join->work_order, $v_cd_sp);
    array_push($join->work_order, $wire_box);
    $symbols = new stdClass();
    $symbols->work_order = new stdClass();
    $symbols->work_order->code = ["equal"];
    $tables = ['work_order', 'v_cd_sp', 'device_box', 'wire_box'];
    $whereAttr = new stdClass();
    $whereAttr->work_order = new stdClass();
    $whereAttr->work_order->code = [$workID];//輸入的工單編號
    $jointype = new stdClass();
    $jointype->work_order_v_cd_sp= "inner";
    $jointype->work_order_device_box= "inner";
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
            'orderby' => ['asc', 'upload_at'],
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
            // $mould['Response'] = "no data";
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
            // $wire_stack['Response'] = "no data";
            // return $wire_stack;
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

    //查詢workhour
    $symbols = new stdClass();
    $symbols->work_code = ["equal"];
    $whereAttr = new stdClass();
    $whereAttr->work_code = [$workID];//輸入的工單編號
    $data = array(
        'condition_1' => array(
            'table' => 'workhour',
            'where' => $whereAttr,
            'orderby' => ['asc', 'upload_at'],
            'symbols' => $symbols
        )
    );
    $workhour = CommonSqlSyntax_Query($data, "PostgreSQL", "workhour");
    if ($workhour['Response'] !== 'ok') {
        return $workhour;
    } else if (count($workhour['QueryTableData']) == 0) {
        // $workhour['Response'] = "no data";
        // return $workhour;
    }
    $workhour_data = $workhour['QueryTableData'];

    $project_array = [];
    for ($i=0; $i < count($work_code_use_data); $i++) { 
        array_push($project_array, $work_code_use_data[$i]['project_id']);
        $project_array = array_unique($project_array);
    }

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
    // $whereAttr->commodity->code = [$workID];//輸入的工單編號
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
    // $project_data = $project['QueryTableData'];

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
        $material_weight = $workorder_related_data[0]['v_cd_sp$plum_weight'] > 0 ? $workorder_related_data[0]['v_cd_sp$standard_weight'] + $workorder_related_data[0]['v_cd_sp$plum_weight'] : round($workorder_related_data[0]['v_cd_sp$standard_weight'] * 1.15, 2);
        $workorder_detail[0] = array(
            // 'device_name' => $work_code_use_data[0]['device_name'],
            'workCode' => $workorder_related_data[0]['work_order$code'],
            'workOrgCode' => $workorder_related_data[0]['work_order$org_code'],
            'work_qty' => $workorder_related_data[0]['work_order$work_qty'],
            'commodity_code' => $workorder_related_data[0]['work_order$commodity_code'],
            'unit_weight' => $unit_weight,
            'standard_weight' => round(($unit_weight * $workorder_related_data[0]['work_order$work_qty']) / 1000, 3),
            'product_name' => $workorder_related_data[0]['v_cd_sp$cd_name'],
            'wire_commodity_code' => $workorder_related_data[0]['work_order$wire_code'],
            'wire_product_name' => $workorder_related_data[0]['wire_box$chinese_name'],
            'material_weight' => $material_weight,
            'wire_need_weight' => round(($material_weight * $workorder_related_data[0]['work_order$work_qty']) / 1000, 3),
            'mould_code' => $workorder_related_data[0]['work_order$mould_code'],
            'control_card' => $workorder_related_data[0]['work_order$control_card'],
            'total_expend' => 0,
            'loss_rate' => 0,
            'total_work_time' => '-',
        );
    } else {
        $workorder_detail[0] = array(
            // 'device_name' => '-',
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
        for ($j=0; $j < count($wire_stack_data); $j++) { 
            if ($wireData[$i]['scroll_no'] == $wire_stack_data[$j]['scroll_no']) {
                $wireData[$i]['furnace_code'] = $wire_stack_data[$j]['furnace_code'];
            }
        }
        if (isset($wireData[$i]['pair'])) {
            $wire_information[$i] = array(
                'code' => $wireData[$i]['scroll_no'],
                'furnaceCode' => $wireData[$i]['furnace_code'],
                'consumption' => $wireData[$i]['weight'] < 0 ? '-' : $wireData[$i]['weight']
            );
        }
        // else {
        //     $wire_information[$i] = array(
        //         'code' => $wireData[$i]['scroll_no'],
        //         'furnace_code' => $wireData[$i]['furnace_code'],
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
            //加總每筆檢驗資料的單支重
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
            $workhour_dataPosition = array_search($work_code_use_data[$i]['project_id'], array_column($total_work_time, 'code'));
            if ($work_code_use_data[$i]['status'] == 'S') {
                if ($total_work_time[$workhour_dataPosition]['startTime'] == '-') {
                    $total_work_time[$workhour_dataPosition]['startTime'] = $work_code_use_data[$i]['upload_at'];
                } else {
                    if (strtotime($total_work_time[$workhour_dataPosition]['startTime']) > strtotime($work_code_use_data[$i]['upload_at'])) {
                        $total_work_time[$workhour_dataPosition]['startTime'] = $work_code_use_data[$i]['upload_at'];
                    }
                }
            } else if ($work_code_use_data[$i]['status'] == 'E') {
                if ($total_work_time[$workhour_dataPosition]['endTime'] == '-') {
                    $total_work_time[$workhour_dataPosition]['endTime'] = $work_code_use_data[$i]['upload_at'];
                } else {
                    if (strtotime($work_code_use_data[$i]['upload_at']) > strtotime($total_work_time[$workhour_dataPosition]['endTime'])) {
                        $total_work_time[$workhour_dataPosition]['endTime'] = $work_code_use_data[$i]['upload_at'];
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
                    'total_time' => '-',
                );
            } else if ($work_code_use_data[$i]['status'] == 'E') {
                $total_work_time[count($total_work_time)] = array(
                    'code' => $work_code_use_data[$i]['project_id'],
                    'device_name' => $work_code_use_data[$i]['device_name'],
                    'startTime' => '-',
                    'endTime' => $work_code_use_data[$i]['upload_at'],
                    'total_time' => '-',
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

