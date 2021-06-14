<?php
function SqlSyntaxQuery_v2($data)
{
    foreach ($data as $condition => $value) {
        (!isset($data[$condition]['fields']))? $data[$condition]['fields']="":"";
        (!isset($data[$condition]['where']))? $data[$condition]['where']="":"";
        (!isset($data[$condition]['orderby']))? $data[$condition]['orderby']="":"";
        (!isset($data[$condition]['limit']))? $data[$condition]['limit']="":"";
        (!isset($data[$condition]['symbols']))? $data[$condition]['symbols']="":"";
        (!isset($data[$condition]['table']))? $data[$condition]['table']="":"";
        (!isset($data[$condition]['intervaltime']))? $data[$condition]['intervaltime']="":"";
        (!isset($data[$condition]['union']))? $data[$condition]['union']="":"";
        if (!isset($data[$condition]['subquery'])) {
            $data[$condition]['subquery'] = "";
        } else {
            $data[$condition]['subquery'] = SqlSyntaxQuery_v2($data[$condition]['subquery']);
        }
    }

    return $data;
}

function SqlSyntaxQuery_v2_5($data)
{
    foreach ($data as $condition => $value) {
        (!isset($data[$condition]['fields']))? $data[$condition]['fields']="":"";
        (!isset($data[$condition]['where']))? $data[$condition]['where']="":"";
        (!isset($data[$condition]['orderby']))? $data[$condition]['orderby']="":"";
        (!isset($data[$condition]['limit']))? $data[$condition]['limit']="":"";
        (!isset($data[$condition]['symbols']))? $data[$condition]['symbols']="":"";
        (!isset($data[$condition]['table']))? $data[$condition]['table']="":"";
        (!isset($data[$condition]['intervaltime']))? $data[$condition]['intervaltime']="":"";
        (!isset($data[$condition]['union']))? $data[$condition]['union']="":"";
        if (!isset($data[$condition]['subquery'])) {
            $data[$condition]['subquery'] = "";
        } else {
            $data[$condition]['subquery'] = SqlSyntaxQuery_v2_5($data[$condition]['subquery']);
        }
    }

    return $data;
}

function SqlSyntaxQueryJoin_v2($data)
{
    foreach ($data as $condition => $value) {
        (!isset($data[$condition]['fields']))? $data[$condition]['fields']="":"";
        (!isset($data[$condition]['where']))? $data[$condition]['where']="":"";
        (!isset($data[$condition]['orderby']))? $data[$condition]['orderby']="":"";
        (!isset($data[$condition]['limit']))? $data[$condition]['limit']="":"";
        (!isset($data[$condition]['symbols']))? $data[$condition]['symbols']="":"";
        (!isset($data[$condition]['table']))? $data[$condition]['table']="":"";
        (!isset($data[$condition]['intervaltime']))? $data[$condition]['intervaltime']="":"";
        (!isset($data[$condition]['union']))? $data[$condition]['union']="":"";
        if (!isset($data[$condition]['subquery'])) {
            $data[$condition]['subquery'] = "";
        } else {
            $data[$condition]['subquery'] = SqlSyntaxQueryJoin_v2($data[$condition]['subquery']);
        }
    }

    return $data;
}

class apiJsonBody_query
{
    public $condition;
    public $fields;
    public $table;
    public $intervaltime;
    public $symbols;
    public $where;
    public $limit;
    public $orderby;
    public $union;
    public $subquery;
    
    public $orderbySort;
    public $union_condition;

    public function __construct($condition = 'condition_1') {
        $this->condition = $condition;
        $this->fields = array();
        $this->table = "";
        $this->intervaltime = new stdClass();
        $this->symbols = new stdClass();
        $this->where = new stdClass();
        $this->limit = array();
        $this->orderby = array();
        $this->union = array();
        $this->subquery = new stdClass();

        $this->orderbySort = "";
        $this->union_condition = new stdClass();
    }

    public function addFields($col_name) {
        array_push($this->fields, $col_name);
    }
    public function setFields($fields_array) {
        if (is_array($fields_array)) {
            $this->fields = $fields_array;
        }
    }

    public function setTable($table_name) {
        if (is_string($table_name)) {
            $this->table = $table_name;
        }        
    }

    public function addIntervaltime($col_name, $data_array) {
        if (!isset($this->intervaltime->{$col_name})) {
            $this->intervaltime->{$col_name} = array();
        }
        array_push($this->intervaltime->{$col_name}, $data_array);
    }
    public function setIntervaltime($intervaltime_obj) {
        $this->intervaltime = $intervaltime_obj;
    }

    public function addSymbols($col_name, $data_string) {
        if (!isset($this->symbols->{$col_name})) {
            $this->symbols->{$col_name} = array();
        }
        array_push($this->symbols->{$col_name}, $data_string);
    }
    public function setSymbols($symbols_obj) {
        $this->symbols = $symbols_obj;
    }

    public function addWhere($col_name, $data_string) {
        if (!isset($this->where->{$col_name})) {
            $this->where->{$col_name} = array();
        }
        array_push($this->where->{$col_name}, $data_string);
    }
    public function setWhere($where_obj) {
        $this->where = $where_obj;
    }

    public function addLimit($data_num) {
        array_push($this->limit, $data_num);
    }
    public function setLimit($data_array) {
        $this->limit = $data_array;
    }

    public function addOrderby($col_name, $sort = null) {
        if (isset($sort)) {
            $this->orderbySort = $sort;
        }
        array_push($this->orderby, $col_name);
    }
    public function setOrderby($data_array) {
        $this->orderbySort = $data_array[0];
        $this->orderby = $data_array;
    }

    public function setUnion($condition, $data_boolean) {
        array_push($this->union, $condition, $data_boolean);
        if (!isset($this->union_condition->{$condition})) {
            $this->union_condition->{$condition} = new stdClass();
        }
        $this->union_condition->{$condition} = new apiJsonBody_query($condition);
    }
    public function getUnion($condition) {
        return $this->union_condition->{$condition};
    }

    public function addSubquery($subcondition) {
        if (!isset($this->subquery->{$subcondition})) {
            $this->subquery->{$subcondition} = new stdClass();
        }
        $this->subquery->{$subcondition} = new apiJsonBody_query($subcondition);
    }
    public function getSubquery($subcondition) {
        return $this->subquery->{$subcondition};
    }
    public function setSubquery($data_obj) {
        $this->subquery = $data_obj;
    }
    public function getApiSubquery() {
        foreach ((array)$this->subquery as $key => $value) {
            $this->subquery->{$key} = $this->subquery->{$key}->getApiJsonBody()[$key];
        }
        return $this->subquery;
    }

    public function getApiJsonBody() {
        $body = array(
            $this->condition => array(
                'fields' => empty($this->fields) ? "" : $this->fields,
                'table' => empty($this->table) ? "" : $this->table,
                'intervaltime' => empty((array)$this->intervaltime) ? "" : $this->intervaltime,
                'symbols' => empty((array)$this->symbols) ? "" : $this->symbols,
                'where' => empty((array)$this->where) ? "" : $this->where,
                'limit' => empty($this->limit) ? "" : $this->limit,
                'orderby' => empty($this->orderby) || empty($this->orderbySort) ? "" : $this->orderby,
                'union' => empty($this->union) ? "" : $this->union,
                'subquery' => empty((array)$this->subquery) ? "" : $this->getApiSubquery()
            )
        );
        //如果有union，加入condition
        if (!empty($this->union)) {
            $union_condition = $this->union_condition->{$this->union[0]}->getApiJsonBody();
            foreach ($union_condition as $key => $value) {
                $body[$key] = $value;
            }
        }
        return $body;
    }
}

class apiJsonBody_queryJoin
{
    public $condition;
    public $fields;
    public $tables;
    public $join;
    public $jointype;
    public $symbols;
    public $where;
    public $limit;
    public $orderby;
    public $subquery;
    
    public $orderbySort;

    public function __construct($condition = 'condition_1') {
        $this->condition = $condition;
        $this->fields = new stdClass();
        $this->tables = array();
        $this->join = new stdClass();
        $this->jointype = new stdClass();
        $this->symbols = new stdClass();
        $this->where = new stdClass();
        $this->limit = array();
        $this->orderby = array();
        $this->subquery = new stdClass();

        $this->orderbySort = "";
    }

    public function addFields($table_name, $col_name_array) {
        if (!isset($this->fields->{$table_name})) {
            $this->fields->{$table_name} = array();
        }
        $this->fields->{$table_name} = $col_name_array;
    }
    public function setFields($fields_obj) {
        $this->fields = $fields_obj;
    }

    public function addTables($table_name) {
        array_push($this->tables, $table_name);
    }
    public function setTables($tables_array) {
        if (is_array($tables_array)) {
            $this->tables = $tables_array;
        }        
    }

    public function setJoin($join_obj) {
        $this->join = $join_obj;
    }
    
    public function addJointype($table_name_1, $table_name_2, $type) {
        $this->jointype->{$table_name_1 . '_' . $table_name_2} = $type;
    }
    public function setJointype($jointype_obj) {
        $this->jointype = $jointype_obj;
    }

    public function addSymbols($table_name, $col_name, $data_string) {
        if (!isset($this->symbols->{$table_name})) {
            $this->symbols->{$table_name} = new stdClass();
        }
        if (!isset($this->symbols->{$table_name}->{$col_name})) {
            $this->symbols->{$table_name}->{$col_name} = array();
        }
        array_push($this->symbols->{$table_name}->{$col_name}, $data_string);
    }
    public function setSymbols($symbols_obj) {
        $this->symbols = $symbols_obj;
    }

    public function addWhere($table_name, $col_name, $data_string) {
        if (!isset($this->where->{$table_name})) {
            $this->where->{$table_name} = new stdClass();
        }
        if (!isset($this->where->{$table_name}->{$col_name})) {
            $this->where->{$table_name}->{$col_name} = array();
        }
        array_push($this->where->{$table_name}->{$col_name}, $data_string);
    }
    public function setWhere($where_obj) {
        $this->where = $where_obj;
    }

    public function addLimit($data_num) {
        array_push($this->limit, $data_num);
    }
    public function setLimit($data_array) {
        $this->limit = $data_array;
    }

    public function addOrderby($table_name, $col_name, $sort = null) {
        if (isset($sort)) {
            $this->orderbySort = $sort;
        }
        array_push($this->orderby, $table_name, $col_name);
    }
    public function setOrderby($data_array) {
        $this->orderbySort = $data_array[0];
        $this->orderby = $data_array;
    }

    public function addSubquery($subcondition) {
        if (!isset($this->subquery->{$subcondition})) {
            $this->subquery->{$subcondition} = new stdClass();
        }
        $this->subquery->{$subcondition} = new apiJsonBody_queryJoin($subcondition);
    }
    public function getSubquery($subcondition) {
        return $this->subquery->{$subcondition};
    }
    public function setSubquery($data_obj) {
        $this->subquery = $data_obj;
    }
    public function getApiSubquery() {
        foreach ((array)$this->subquery as $key => $value) {
            $this->subquery->{$key} = $this->subquery->{$key}->getApiJsonBody()[$key];
        }
        return $this->subquery;
    }

    public function getApiJsonBody() {
        $body = array(
            $this->condition => array(
                'fields' => empty((array)$this->fields) ? "" : $this->fields,
                'tables' => empty($this->tables) ? "" : $this->tables,
                'join' => empty((array)$this->join) ? "" : $this->join,
                'jointype' => empty((array)$this->jointype) ? "" : $this->jointype,
                'symbols' => empty((array)$this->symbols) ? "" : $this->symbols,
                'where' => empty((array)$this->where) ? "" : $this->where,
                'limit' => empty($this->limit) ? "" : $this->limit,
                'orderby' => empty($this->orderby) || empty($this->orderbySort) ? "" : $this->orderby,
                'subquery' => empty((array)$this->subquery) ? "" : $this->getApiSubquery()
            )
        );
        return $body;
    }
}
?>