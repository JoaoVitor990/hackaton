<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);


session_start();

define('HOST', 'localhost');
define('USER', 'root');
define('PASS', 'usbw');
define('BASE', 'login');

// Criar conexão
$conn = new mysqli(HOST, USER, PASS, BASE);

// Verificar conexão
if ($conn->connect_error) {
    die("Falha na conexão: " . $conn->connect_error);
}

$msg = "";

// Login
if (isset($_POST['login'])) {
    if (!empty($_POST['email']) && !empty($_POST['senha'])) {
        $email = $_POST['email'];
        $senha = $_POST['senha'];

        $stmt = $conn->prepare("SELECT * FROM usuarios WHERE email = ?");
        $stmt->bind_param("s", $email);
        $stmt->execute();
        $result = $stmt->get_result();

        if ($result->num_rows === 1) {
            $user = $result->fetch_assoc();
            if (password_verify($senha, $user['senha'])) {
                // Verifica se é admin
                if ($email === 'admin@gmail.com') {
                    $_SESSION['admin'] = true;
                    $_SESSION['user_id'] = $user['id'];
                    $_SESSION['email'] = $email;
                    header("Location: ../blog/admin.php"); // redireciona para área admin
                    exit;
                } else {
                    $_SESSION['user_id'] = $user['id'];
                    $_SESSION['email'] = $email;
                    header("Location: index.html"); // área do usuário normal
                    exit;
                }
            } else {
                $msg = "Senha incorreta!";
            }
        } else {
            $msg = "Usuário não encontrado!";
        }
        $stmt->close();
    } else {
        $msg = "Preencha todos os campos para entrar!";
    }
}

$conn->close();
?>
<!DOCTYPE html>
<html lang="pt-BR">
    <link rel="stylesheet" href="login.css">
<head>
    <meta charset="UTF-8" />
    <title>Login</title>
    <link rel="icon" type="image/png" href="AxionSCAN.png" sizes="32x32">
</head>
<body>

    <div class="login">
    <form method="POST" action="">
        <h1 id="login">Login</h1>
        <label>
            <h3 class="cod_professor">Codigo do professor</h3>
            <input name="email" required id="campo_gmail"/>
        </label>
        <br/><br/>
        <label>
            <h3 class="senha">Senha</h3>
            <input type="password" name="senha" required id="campo_senha"/>
        </label>

        <br/><br/>

        <button type="submit" name="login" class="logar">Login</button>
        <br><br>
       <a href="registro.php" id="criar_cont" >Ainda não tem uma conta? Crie aqui!</a><br><br>
    </form>
    </div>

</body>
</html>
