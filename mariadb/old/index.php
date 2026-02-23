<html>
 <head>
  <title>PHP-Test</title>
 </head>
 <body>


<?php


/*
  Rui Santos
  Complete project details at https://RandomNerdTutorials.com/esp32-esp8266-mysql-database-php/
  
  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files.
  
  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.
*/


$servername = "localhost";

// REPLACE with your Database name
$dbname = "home";
// REPLACE with Database user
$username = "db";
// REPLACE with Database user password
$password = "9wertzuioP!!";

// Keep this API Key value to be compatible with the ESP32 code provided in the project page. 
// If you change this value, the ESP32 sketch needs to match
$api_key_tempAndHum = "3445KLF8SD8";
$api_key_event = "2398KSFH23J";

$api_key = $body = $json = "";

// echo $_SERVER["REQUEST_METHOD"];

if ($_SERVER["REQUEST_METHOD"] == "POST") {
	
	$body = file_get_contents('php://input');
	$json = json_decode($body);
	
	// var_dump($json);
	// echo "\n";
	
    // $api_key = test_input($_POST["api_key"]);
    $api_key = test_input($json->api_key);
	// echo $api_key;
    if($api_key == $api_key_tempAndHum) {
		$officeTemp = test_input($json->officeTemp);
		$badTemp = test_input($json->badTemp);
		$wcTemp = test_input($json->wcTemp);
		$szTemp = test_input($json->szTemp);
		$wzTemp = test_input($json->wzTemp);
		$floorTemp = test_input($json->floorTemp);
		$officeHum = test_input($json->officeHum);
		$badHum = test_input($json->badHum);
		$wcHum = test_input($json->wcHum);
		$szHum = test_input($json->szHum);
		$wzHum = test_input($json->wzHum);
		$floorHum = test_input($json->floorHum);

		// Create connection
		$conn = new mysqli($servername, $username, $password, $dbname);
		// Check connection
		if ($conn->connect_error) {
			die("Connection failed: " . $conn->connect_error);
		} 
		
		$sql = "INSERT INTO TempAndHum (officeTemp, badTemp, wcTemp, szTemp, wzTemp, floorTemp, officeHum, badHum, wcHum, szHum, wzHum, floorHum)
		VALUES ('" . $officeTemp . "', '" . $badTemp . "', '" . $wcTemp . "', '" . $szTemp . "', '" . $wzTemp . "', '" . $floorTemp . "', '" . $officeHum . "', '" . $badHum . "', '" . $wcHum . "', '" . $szHum . "', '" . $wzHum . "', '" . $floorHum . "')";
		
		if ($conn->query($sql) === TRUE) {
			echo "New record created successfully";
		} 
		else {
			echo "Error: " . $sql . "<br>" . $conn->error;
		}
	
		$conn->close();
    }
    else if($api_key == $api_key_event) {
		
		// Create connection
		$conn = new mysqli($servername, $username, $password, $dbname);
		// Check connection
		if ($conn->connect_error) {
			die("Connection failed: " . $conn->connect_error);
		} 		
		
		$type = test_input($json->type);
		if ($type == "movement") {
			$source = test_input($json->source);
			$active = test_input($json->active);
			
			$sql = "INSERT INTO Movement (source, active)
			VALUES ('" . $source . "', '" . $active . "')";
		}
		else if ($type == "analog") {
			$source = test_input($json->source);
			$value = test_input($json->value);
			
			$sql = "INSERT INTO HeatAndBright (source, value)
			VALUES ('" . $source . "', '" . $value . "')";		
		}

		if ($conn->query($sql) === TRUE) {
			echo "New record created successfully";
		} 
		else {
			echo "Error: " . $sql . "<br>" . $conn->error;
		}

		$conn->close();
		

			
    }
    else {
        echo "Wrong API Key provided.";
    }

}
else {
    echo "No data posted with HTTP POST.";
}

function test_input($data) {
    $data = trim($data);
    $data = stripslashes($data);
    $data = htmlspecialchars($data);
    return $data;
}

?>

 </body>
</html>