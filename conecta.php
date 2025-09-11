<?php
$host = 'localhost';
$user = 'root';
$password = 'usbw';
$db = 'login';

$conn = new mysqli($host, $user, $password, $db);

if ($conn->connect_error) {
    die('Conexão falhou: ' . $conn->connect_error);
}
?>