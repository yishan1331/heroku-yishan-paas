<?php
function CommonSqlSyntax_Query($data, $database, $check_json = 'yes')
{
    global $publicIP,$publicPort;
    if ($check_json == 'no') {
        $postdata = $data;
    } else {
        $postdata = SqlSyntaxQuery_v2($data);
    }

    if ($database == 'PostgreSQL') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/2.0/myps/Sensor/SqlSyntax?uid=@sapido@PaaS&getSqlSyntax=yes";
    } else if ($database == 'MySQL') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/2.0/my/CommonUse/SqlSyntax?uid=@sapido@PaaS&getSqlSyntax=yes";
    } else if ($database == 'MsSQL') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/2.0/ms/CommonUse/SqlSyntax?uid=@sapido@PaaS&getSqlSyntax=yes";
    }

    $returnData = connection($url, 'POST', $postdata);
    return $returnData;
}

function CommonSqlSyntax_Query_v2_5($data, $database, $check_json = 'yes')
{
    global $publicIP,$publicPort;
    if ($check_json == 'no') {
        $postdata = $data;
    } else {
        $postdata = SqlSyntaxQuery_v2_5($data);
    }

    if ($database == 'PostgreSQL') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/2.5/myps/Sensor/SqlSyntax?uid=@sapido@PaaS&dbName=site2&getSqlSyntax=yes";
    }

    $returnData = connection($url, 'POST', $postdata);
    return $returnData;
}

function CommonSqlSyntaxJoin_Query($data, $database, $check_json = 'yes')
{
    global $publicIP,$publicPort;
    if ($check_json == 'no') {
        $postdata = $data;
    } else {
        $postdata = SqlSyntaxQueryJoin_v2($data);
    }

    if ($database == 'PostgreSQL') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/2.0/myps/Sensor/SqlSyntax/JoinMultiTable?uid=@sapido@PaaS&getSqlSyntax=yes";
    } else if ($database == 'MySQL') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/2.0/my/CommonUse/SqlSyntax/JoinMultiTable?uid=@sapido@PaaS&getSqlSyntax=yes";
    } else if ($database == 'MsSQL') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/2.0/ms/CommonUse/SqlSyntax/JoinMultiTable?uid=@sapido@PaaS&getSqlSyntax=yes";
    }

    $returnData = connection($url, 'POST', $postdata);
    return $returnData;
}

function CommonIntervalQuery($data, $database, $teble)
{
    global $publicIP,$publicPort;

    if ($database == 'PostgreSQL') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/2.0/myps/Sensor/Interval/" . $teble . "?uid=@sapido@PaaS&attr=" . $data['col'] . "&valueStart=" . $data['valueStart'] . "&valueEnd=" . $data['valueEnd'];
    } else if ($database == 'MySQL') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/1.0/my/CommonUse/Interval/" . $teble . "?uid=@sapido@PaaS&attr=" . $data['col'] . "&valueStart=" . $data['valueStart'] . "&valueEnd=" . $data['valueEnd'];
    } else if ($database == 'MsSQL') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/1.0/ms/CommonUse/Interval/" . $teble . "?uid=@sapido@PaaS&attr=" . $data['col'] . "&valueStart=" . $data['valueStart'] . "&valueEnd=" . $data['valueEnd'];
    }

    $returnData = connection($url, 'GET');
    return $returnData;
}

function CommonSpecificKeyQuery($database, $teble, $pattern)
{
    global $publicIP,$publicPort;

    if ($database == 'Redis') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/1.0/rd/CommonUse/SpecificKey/mes_device_status_" . $teble . "?uid=@sapido@PaaS&pattern=" . $pattern;
    }

    $returnData = connection($url, 'GET');
    return $returnData;
}

function SensorSingleRowQuery($data, $database, $teble)
{
    global $publicIP,$publicPort;

    if ($database == 'PostgreSQL') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/1.0/myps/Sensor/SingleRow/" . $data['querySingle'] . "/" . $teble . "?uid=@sapido@PaaS";
    }

    $returnData = connection($url, 'GET');
    return $returnData;
}

function CommonTableQuery($database, $teble)
{
    global $publicIP,$publicPort;

    if ($database == 'MySQL') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/1.0/my/CommonUse/TableData?table=" . $teble . "&uid=@sapido@PaaS";
    }

    $returnData = connection($url, 'GET');
    return $returnData;
}

function CommonUpdate($data, $database, $teble)
{
    global $publicIP,$publicPort;

    if ($database == 'MySQL') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/1.5/my/CommonUse/" . $teble . "?uid=@sapido@PaaS";
    } else if ($database == 'MsSQL') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/1.5/ms/CommonUse/" . $teble . "?uid=@sapido@PaaS";
    } else if ($database == 'Redis') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/1.0/rd/CommonUse/Hash/Keys/SpecificField?uid=@sapido@PaaS";
    }

    $returnData = connection($url, 'PATCH', $data);
    return $returnData;
}

function CommonDelete($data, $database, $teble)
{
    global $publicIP,$publicPort;

    if ($database == 'MySQL') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/1.5/my/CommonUse/" . $teble . "?uid=@sapido@PaaS";
    }

    $returnData = connection($url, 'DELETE', $data);
    return $returnData;
}

function ExportCsv($data, $database, $teble)
{   
    global $publicIP,$publicPort;
    if ($database == 'PostgreSQL') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/1.0/myps/Sensor/ExportCsv/" . $teble . "?uid=@sapido@PaaS";
    }

    $returnData = connection($url, 'POST', $data);
    return $returnData;
}

function CommonCreate($data, $database, $teble)
{
    global $publicIP,$publicPort;
    if ($database == 'PostgreSQL') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/2.0/myps/Sensor/Rows/" . $teble . "?uid=@sapido@PaaS";
    } else if ($database == 'MySQL') {
        $url = "https://" . $publicIP . ":" . $publicPort. "/api/CHUNZU/1.5/my/CommonUse/" . $teble . "?uid=@sapido@PaaS";
    }
    
    $returnData = connection($url, 'POST', $data);
    return $returnData;
}
?>