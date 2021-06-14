<?php
function connection($url, $methods, $data = null)
{
    if ($methods == "GET"){
        $options = array(
            "ssl"=>array(
                "verify_peer"=>false,
                "verify_peer_name"=>false,
            ),
        );
    } else {
        $options = array(
            'http' => array(
                'method' => $methods,
                'content' => json_encode($data),
                'header' => "Content-Type: application/json\r\n" .
                "Accept: application/json\r\n"
            ),
            "ssl"=>array(
                "verify_peer"=>false,
                "verify_peer_name"=>false,
            ),
        );
    }
    $context = stream_context_create($options);
    $result = file_get_contents($url, false, $context);
    $Arr = json_decode($result, true);
 
    return $Arr;
}
?>