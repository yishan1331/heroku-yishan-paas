<?php
function update($params)
{
    return CommonUpdate($params->postdata, $params->database, $params->table);
};

function userUpdate($params)
{
    global $publicIP,$publicPort;
    $returnData = connection("https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/1.0/my/user/update_User?uid=@sapido@PaaS", $params->methods, $params->postdata);
    return $returnData;
};

function deviceUpdate($params)
{
    global $publicIP,$publicPort;
    $returnData = connection("https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/1.0/Customized/Device/Macro?uid=@sapido@PaaS", $params->methods, $params->postdata);
    return $returnData;
};

function deviceTypeUpdate($params)
{
    global $publicIP,$publicPort;
    $returnData = connection("https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/1.0/Customized/DeviceType/Macro?uid=@sapido@PaaS", $params->methods, $params->postdata);
    return $returnData;
};

function CommonJoinMultiTable($params)
{
    global $publicIP,$publicPort;
    $postdata = new stdClass();
    foreach ($params->condition as $key => $value) {
        $postdata->$key = new stdClass();
        (!property_exists($value, 'tables')) ? $tables = "" : $tables = $value->tables;
        (!property_exists($value, 'fields')) ? $fields = "" : $fields = $value->fields;
        (!property_exists($value, 'orderby')) ? $orderby = "" : $orderby = $value->orderby;
        (!property_exists($value, 'limit')) ? $limit = "" : $limit = $value->limit;
        (!property_exists($value, 'where')) ? $where = "" : $where = $value->where;
        (!property_exists($value, 'symbols')) ? $symbols = "" : $symbols = $value->symbols;
        (!property_exists($value, 'join')) ? $join = "" : $join = $value->join;
        (!property_exists($value, 'jointype')) ? $jointype = "" : $jointype = $value->jointype;
        (!property_exists($value, 'subquery')) ? $subquery = "" : $subquery = $value->subquery;
        $postdata->$key->tables = $tables;
        $postdata->$key->fields = $fields;
        $postdata->$key->orderby = $orderby;
        $postdata->$key->limit = $limit;
        $postdata->$key->where = $where;
        $postdata->$key->symbols = $symbols;
        $postdata->$key->join = $join;
        $postdata->$key->jointype = $jointype;
        $postdata->$key->subquery = $subquery;
    }

    $returnData = connection("https://" . $publicIP . ":" . $publicPort. "/2.0/my/CommonUse/SqlSyntax/JoinMultiTable?uid=@sapido@PaaS&getSqlSyntax=yes", $params->methods, $postdata);
    return $returnData;
}
