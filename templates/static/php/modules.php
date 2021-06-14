<?php
date_default_timezone_set("Asia/Taipei");
$postBody = file_get_contents("php://input");
$postBody = json_decode($postBody);
$methods = $postBody->methods;
$whichFunction = $postBody->whichFunction;
include("./globalvar.php");
include("./api.php");
include("./apiJsonBody.php");
include("./connection.php");
include("./commonFunction.php");

if (isset($postBody->vuePage)) {
    $vuePage = ['elecboard', 'machstatus', 'yieldstatistics', 'activation', 'operatelog', 'alarmhistory', 'workorderhistory', 'qualityinsp', 'systemset', 'machmalfunction', 'testpage', 'devicesetting','overview','inspectionrecord','devicemanage','diagnosis','abnormal','aicontrol'];
    $vue_pageSelect = $postBody->vuePage;
    if (in_array($vue_pageSelect,$vuePage,true)){
        $vue_pagePosition = array_search($vue_pageSelect,$vuePage,true);
        include("./views/" . $vuePage[$vue_pagePosition] . ".php");
    }
} else {
    include("./views/common.php");
}

$getData = $whichFunction($postBody);
echo json_encode($getData);
