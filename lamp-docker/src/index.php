<!-- <?php
// Database configuration
$host = 'mysql';
$dbname = 'student_db';
$user = 'WINstudent';
$pass = 'sutdent999999';
$port = 3306;

// Enable error reporting
error_reporting(E_ALL);
ini_set('display_errors', 1);

try {
    // Create PDO connection
    $conn = new PDO(
        "mysql:host=$host;port=$port;dbname=$dbname;charset=utf8mb4",
        $user,
        $pass,
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false
        ]
    );

    // Process form submission
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        // Validate and sanitize inputs
        $student_id = filter_input(INPUT_POST, 'student_id', FILTER_VALIDATE_INT);
        $name = filter_input(INPUT_POST, 'name', FILTER_SANITIZE_STRING);
        $subject = filter_input(INPUT_POST, 'subject', FILTER_SANITIZE_STRING);

        // Validate inputs
        if (!$student_id || empty($name) || empty($subject)) {
            throw new Exception("All fields are required and student ID must be a number");
        }

        // Check if student ID already exists
        $check_stmt = $conn->prepare("SELECT student_id FROM student WHERE student_id = ?");
        $check_stmt->execute([$student_id]);
        
        if ($check_stmt->rowCount() > 0) {
            throw new Exception("Student ID already exists");
        }

        // Insert new student
        $insert_stmt = $conn->prepare("INSERT INTO student 
                                    (student_id, name, subject) 
                                    VALUES (?, ?, ?)");
        $insert_stmt->execute([$student_id, $name, $subject]);

        echo "<div class='success'>Student record created successfully!</div>";
    }
} catch(PDOException $e) {
    echo "<div class='error'>Database Error: " . htmlspecialchars($e->getMessage()) . "</div>";
} catch(Exception $e) {
    echo "<div class='error'>Error: " . htmlspecialchars($e->getMessage()) . "</div>";
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Student Registration</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 2rem auto; padding: 0 1rem; }
        .container { background: #f8f9fa; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .form-group { margin-bottom: 1.5rem; }
        label { display: block; margin-bottom: 0.5rem; font-weight: 600; color: #2d3748; }
        input { width: 100%; padding: 0.75rem; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box; }
        button { background: #4299e1; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #3182ce; }
        .success { color: #2f855a; background: #f0fff4; padding: 1rem; margin: 1rem 0; border-radius: 4px; }
        .error { color: #c53030; background: #fff5f5; padding: 1rem; margin: 1rem 0; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Student Registration</h2>
        <form method="POST">
            <div class="form-group">
                <label for="student_id">Student ID:</label>
                <input type="number" id="student_id" name="student_id" 
                       required min="1" 
                       title="Must be a unique number">
            </div>
            
            <div class="form-group">
                <label for="name">Full Name:</label>
                <input type="text" id="name" name="name" 
                       required pattern="[A-Za-z ]{3,50}" 
                       title="3-50 letters and spaces">
            </div>

            <div class="form-group">
                <label for="subject">Subject:</label>
                <input type="text" id="subject" name="subject" 
                       required pattern="[A-Za-z0-9 &-]{3,50}" 
                       title="3-50 characters (letters, numbers, &, - or space)">
            </div>

            <button type="submit">Register Student</button>
        </form>
    </div>
</body>
</html> -->
<?php
// Database configuration
$host = 'mysql';
$dbname = 'student_db';
$user = 'WINstudent';
$pass = 'sutdent999999';
$port = 3306;

try {
    // Create PDO connection
    $conn = new PDO(
        "mysql:host=$host;port=$port;dbname=$dbname;charset=utf8mb4",
        $user,
        $pass,
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
        ]
    );

    // Fetch messages
    $stmt = $conn->query("SELECT * FROM messages ORDER BY created_at DESC");
    $messages = $stmt->fetchAll();

} catch(PDOException $e) {
    die("<div class='error'>Database Error: " . htmlspecialchars($e->getMessage()) . "</div>");
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inspirational Messages</title>
    <style>
        body { 
            font-family: 'Arial', sans-serif; 
            max-width: 800px; 
            margin: 2rem auto; 
            padding: 0 1rem;
        }
        .message-container {
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .message-card {
            padding: 1.5rem;
            border-bottom: 1px solid #eee;
        }
        .message-card:last-child {
            border-bottom: none;
        }
        .message-text {
            font-size: 1.1rem;
            line-height: 1.6;
            color: #333;
        }
        .timestamp {
            font-size: 0.9rem;
            color: #666;
            margin-top: 0.5rem;
        }
        .header {
            text-align: center;
            color: #2d3748;
            margin-bottom: 2rem;
        }
    </style>
</head>
<body>
    <h1 class="header">Inspirational Messages</h1>
    
    <div class="message-container">
        <?php if (!empty($messages)): ?>
            <?php foreach ($messages as $message): ?>
                <div class="message-card">
                    <p class="message-text"><?= htmlspecialchars($message['message']) ?></p>
                    <div class="timestamp">
                        Posted on: <?= date('F j, Y \a\t g:i a', strtotime($message['created_at'])) ?>
                    </div>
                </div>
            <?php endforeach; ?>
        <?php else: ?>
            <div class="message-card">
                <p class="message-text">No messages found</p>
            </div>
        <?php endif; ?>
    </div>
</body>
</html>