<?php

session_start();

require 'conecta.php';
$msg = "";

// Registro
if (isset($_POST['registrar'])) {
    if (!empty($_POST['nome']) && !empty($_POST['codigo_professor']) && !empty($_POST['senha'])) {
        $nome  = $_POST['nome'];
        $codigo_professor = $_POST['codigo_professor'];
        $senhaOriginal = $_POST['senha'];

        // Validação da senha
        if (strlen($senhaOriginal) < 8 || 
            !preg_match('/[0-9]/', $senhaOriginal) || 
            !preg_match('/[\W_]/', $senhaOriginal)) {
            $msg = "A senha deve conter no mínimo 8 caracteres, incluindo pelo menos 1 número e 1 caractere especial.";
        } else {
            $senha = password_hash($senhaOriginal, PASSWORD_DEFAULT);

            $stmt = $conn->prepare("SELECT * FROM usuarios WHERE codigo_professor = ?");
            $stmt->bind_param("s", $codigo_professor);
            $stmt->execute();
            $result = $stmt->get_result();

            if ($result->num_rows > 0) {
                $msg = "Usuário já existe!";
            } else {
                $stmt = $conn->prepare("INSERT INTO usuarios (nome, codigo_professor, senha) VALUES (?, ?, ?)");
                $stmt->bind_param("sss", $nome, $codigo_professor, $senha);
                if ($stmt->execute()) {
                    $msg = "Registrado com sucesso!";
                    header("Refresh: 2; url=login.php");
                    exit;
                } else {
                    $msg = "Erro no registro!";
                }
            }
        }
    } else {
        $msg = "Preencha todos os campos para registrar!";
    }
}
$conn->close();
?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8" />
    <title>Registro</title>
     <link rel="stylesheet" href="css.css">
</head>
<body>

    <form method="POST" action="">
        <label>
            <input type="text" name="nome" required placeholder="Nome"/>
        </label><br/><br/>

        <label>
            <input name="codigo_professor" required placeholder="codigo_professor"/>
        </label><br/><br/>

        <label>
            <input type="password" name="senha" required
                   pattern="^(?=.*[0-9])(?=.*[\W_]).{8,}$"
                   title="A senha deve ter no mínimo 8 caracteres, incluindo ao menos 1 número e 1 caractere especial." placeholder="Senha"/>
        </label><br/><br/>

        <button type="submit" name="registrar">Registrar</button><br/><br/>

        <a href="login.php">Já tem uma conta? Entre agora!</a>
    </form>

</body>
</html>