<?php
function TimeSubtraction($startTime, $endTime, $type)
{
    if (strtotime($endTime) > strtotime($startTime)) {
        $time = strtotime($endTime)-strtotime($startTime);
        $returnData = [];
        if ($type == 'hour') {
            $date = floor($time / 86400);
            $hour = floor($time % 86400 / 3600);
            $minute = floor($time % 86400 / 60) - $hour * 60;
            $second = floor($time % 86400 % 60);

            $hour = $hour + $date * 24; // 相加小時數
            
            $hour < 10 ? $showHour = '0' . $hour : $showHour = $hour;
            $minute < 10 ? $showMinute = '0' . $minute : $showMinute = $minute;
            $second < 10 ? $showSecond = '0' . $second : $showSecond = $second;
            $returnData[0] = $showHour . ":" . $showMinute . ":" . $showSecond;
    
            $returnData[1] = "";
            if ($hour > 0) {
                $returnData[1] .= $hour . "小時";
            }
            if ($minute > 0) {
                $returnData[1] .= $minute . "分鐘";
            }
            if ($second > 0) {
                $returnData[1] .= $second . "秒";
            }
            $returnData[2] = $time;
            return $returnData;
        } else if ($type == 'date') {
            $date = floor($time / 86400);
            $hour = floor($time % 86400 / 3600);
            $minute = floor($time % 86400 / 60) - $hour * 60;
            $second = floor($time % 86400 % 60);
    
            $date < 10 ? $showDate = '0' . $date : $showDate = $date;
            $hour < 10 ? $showHour = '0' . $hour : $showHour = $hour;
            $minute < 10 ? $showMinute = '0' . $minute : $showMinute = $minute;
            $second < 10 ? $showSecond = '0' . $second : $showSecond = $second;
            $returnData[0] = $showDate . " " . $showHour . ":" . $showMinute . ":" . $showSecond;
            
            $returnData[1] = "";
            if ($date > 0) {
                $returnData[1] .= $date . "天";
            }
            if ($hour > 0) {
                $returnData[1] .= $hour . "小時";
            }
            if ($minute > 0) {
                $returnData[1] .= $minute . "分鐘";
            }
            if ($second > 0) {
                $returnData[1] .= $second . "秒";
            }
            $returnData[2] = $time;
            return $returnData;
        }
    } else {
        if ($type == 'hour') {
            $returnData[0] = "0:0:0";
            $returnData[1] = "0秒";
            $returnData[2] = 0;
            return $returnData;
        } else if ($type == 'date') {
            $returnData[0] = "0 0:0:0";
            $returnData[1] = "0秒";
            $returnData[2] = 0;
            return $returnData;
        }
        // $returnData = ['$startTime > $endTime'];
    }
}