
<?php
ini_set('display_errors', 0);
ini_set('display_startup_errors', 0);
error_reporting(E_ALL);

ignore_user_abort(true);
set_time_limit(0);

$API_KEY = "6521772278:AAGGcUfdThIHdFcXWC7wFFdTf6stMPnSasA";
$ADMIN = 7037031402;

define('DB_HOST', 'localhost');
define('DB_USER', 'SSFSBOT');
define('DB_PASS', 'Sa12345Ut');
define('DB_NAME', 'SSFSBOT');

define('API_KEY', $API_KEY);
define('ADMIN', $ADMIN);
define('IDBot', explode(':', $API_KEY)[0]);
$bot_id = explode(':', API_KEY)[0];

class MySQLDB {
    private static $connection = null;
    private $tableName;

    public function __construct($tableName) {
        $this->tableName = preg_replace('/[^a-zA-Z0-9_]/', '', $tableName);

        if (self::$connection === null) {
            self::$connection = new mysqli(DB_HOST, DB_USER, DB_PASS, DB_NAME);
            if (self::$connection->connect_error) {
                error_log("MySQL Connection Failed: " . self::$connection->connect_error);
                die("Database connection failed. Please check your configuration.");
            }
            self::$connection->set_charset("utf8mb4");
        }

        $this->createTableIfNotExists();
    }

    private function createTableIfNotExists() {
        $sql = "CREATE TABLE IF NOT EXISTS `{$this->tableName}` (
                    `key` VARCHAR(255) PRIMARY KEY,
                    `value` LONGTEXT NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";
        
        if (!self::$connection->query($sql)) {
            error_log("Failed to create table {$this->tableName}: " . self::$connection->error);
            die("Database table creation failed.");
        }
    }

    public function set($key, $value) {
        $jsonValue = json_encode($value, JSON_UNESCAPED_UNICODE);
        $stmt = self::$connection->prepare(
            "INSERT INTO `{$this->tableName}` (`key`, `value`) VALUES (?, ?) 
             ON DUPLICATE KEY UPDATE `value` = VALUES(`value`)"
        );
        if ($stmt === false) { error_log("Prepare failed: (" . self::$connection->errno . ") " . self::$connection->error); return false; }
        $stmt->bind_param("ss", $key, $jsonValue);
        $result = $stmt->execute();
        $stmt->close();
        return $result;
    }

    public function get($key) {
        $stmt = self::$connection->prepare("SELECT `value` FROM `{$this->tableName}` WHERE `key` = ?");
        if ($stmt === false) { error_log("Prepare failed: (" . self::$connection->errno . ") " . self::$connection->error); return null; }
        $stmt->bind_param("s", $key);
        $stmt->execute();
        $result = $stmt->get_result();
        $row = $result->fetch_assoc();
        $stmt->close();
        return $row ? json_decode($row['value'], true) : null;
    }

    public function delete($key) {
        $stmt = self::$connection->prepare("DELETE FROM `{$this->tableName}` WHERE `key` = ?");
        if ($stmt === false) { error_log("Prepare failed: (" . self::$connection->errno . ") " . self::$connection->error); return false; }
        $stmt->bind_param("s", $key);
        $result = $stmt->execute();
        $stmt->close();
        return $result;
    }

    public function clear() {
        return self::$connection->query("TRUNCATE TABLE `{$this->tableName}`");
    }

    public function getAllWithPrefix($prefix) {
        $stmt = self::$connection->prepare("SELECT `key`, `value` FROM `{$this->tableName}` WHERE `key` LIKE ?");
        if ($stmt === false) { error_log("Prepare failed: (" . self::$connection->errno . ") " . self::$connection->error); return []; }
        $prefixParam = $prefix . '%';
        $stmt->bind_param('s', $prefixParam);
        $stmt->execute();
        $result = $stmt->get_result();
        $data = [];
        while ($row = $result->fetch_assoc()) {
            $data[$row['key']] = json_decode($row['value'], true);
        }
        $stmt->close();
        return $data;
    }
}


$wallets = new MySQLDB("user_wallets");
$bot = new MySQLDB("bot_settings");
$funding = new MySQLDB("funding_channels");
$users = new MySQLDB("users_data");
$sessions = new MySQLDB("user_sessions");
$security = new MySQLDB("access_control");
$cache = new MySQLDB("system_cache");
$forced_join = new MySQLDB("forced_subscriptions");
$referral_system = new MySQLDB("referral_system");
$orders = new MySQLDB("orders_history");
$stats = new MySQLDB("bot_statistics");
$auto_replies = new MySQLDB("auto_responses");
$join_tracker = new MySQLDB("subscription_tracker");
$button_data = new MySQLDB("button_data");
$invite_logs = new MySQLDB("invite_logs");

function bot($method, $datas = []) {
    global $wallets, $bot;
    $Y = false; 
    if (isset($datas['reply_markup'])) {
        $markup = json_decode($datas['reply_markup']);
        if (isset($markup->inline_keyboard)) {
            $AZRARS = $bot->get("AZRARSOx") ?? [];
            foreach ($markup->inline_keyboard as $rowIndex => $row) {
                foreach ($row as $buttonIndex => $button) {
                    foreach ($AZRARS as $index => $added_button) {
                        $added_buttonx = $bot->get("AZRARS_X_" . $added_button);

                        if ($added_button == '✅ ژمارەی داواکارییەکان :  ✅' && preg_match('/ژمارەی داواکارییەکان /', $button->text)) {
                            if (preg_match('/\d+/', $button->text, $matches) && !$Y) {
                                $Y = true;
                                $order_count = (int)$matches[0];
                                $button->text = preg_replace('/\d+/', '', $button->text);
                            }
                        }

                        if ($button->text == $added_button) {
                            if ($Y) {
                                $as = explode(':', $added_buttonx);
                                $ao = $as[0] . ": " . $order_count . "" . $as[1];
                                $added_buttonx = $ao;
                            }
                            $markup->inline_keyboard[$rowIndex][$buttonIndex]->text = $added_buttonx;
                        }
                    }
                }
            }
            $datas['reply_markup'] = json_encode($markup);
        }
    }

    $restriction = $bot->get('HIMAIA_restriction');
    if ($restriction == '✅') {
        $datas['protect_content'] = true;
    }

    if ($bot->get('HIMAIA_restriction_media') == '✅' && strtolower($method) != "sendmessage") {
        $datas['protect_content'] = true;
    }

    if ($bot->get('HIMAIA_restriction_text') == '✅' && strtolower($method) == "sendmessage") {
        $datas['protect_content'] = true;
    }

    if ($bot->get('HIMAIA_restriction_LINK') == '✅' && isset($datas['text']) && preg_match('/https/', strtolower($datas['text']))) {
        $datas['protect_content'] = true;
    }

    $url = "https://api.telegram.org/bot" . API_KEY . "/" . $method;

    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $datas);
    
    $response = curl_exec($ch);
    
    if (curl_errno($ch)) {
        error_log("cURL Error: " . curl_error($ch));
        curl_close($ch); 
        return false;
    }

    curl_close($ch);
    
    return json_decode($response);
}

if ($bot->get('setup_status_v2') !== 'completed') {
    $webhook_url = "https://" . $_SERVER['HTTP_HOST'] . $_SERVER['SCRIPT_NAME'];
    
    bot('setWebhook', [
        'url' => $webhook_url,
        'drop_pending_updates' => true,
    ]);

    $cmd_list = $bot->get('cmd_list') ?: [];
    if (!in_array('start', $cmd_list)) {
        $cmd_list[] = 'start';
        $bot->set('cmd_start', 'دەستپێکردن');
        $bot->set('cmd_list', $cmd_list);
    }
    $Commands = [];
    foreach (array_reverse($cmd_list) as $cmd) {
        $desc = $bot->get('cmd_' . $cmd) ?: 'وەسف بوونی نییە';
        $Commands[] = ['command' => $cmd, 'description' => $desc];
    }
    bot('setMyCommands', [
        'commands' => json_encode($Commands)
    ]);
    $bot->set('setup_status_v2', 'completed');
}
$usrbot = $bot->get('bot_username');

if (!$usrbot) {
    $getMe = bot("getme");
    if ($getMe && isset($getMe->result->username)) {
        $usrbot = $getMe->result->username;
        $bot->set('bot_username', $usrbot);
    } else {
        $usrbot = "YourBotUsername";
        error_log("Failed to get bot username.");
    }
}

define("USR_BOT", $usrbot);
$USRBOT = $usrbot;

date_default_timezone_set('Asia/Baghdad');

function TMOIL($API_KEY, $method, $datas = []) {
    $url = "https://api.telegram.org/bot" . $API_KEY . "/" . $method;
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $datas);
    $response = curl_exec($ch);
    if (curl_errno($ch)) {
        error_log("cURL Error in TMOIL: " . curl_error($ch));
        return false;
    }
    curl_close($ch);
    return json_decode($response);
}

function br($method, $datas = []) {
    return TMOIL(API_KEY, $method, $datas);
}

function sendCaptcha($chat_id, $bot_token = API_KEY) {
    $code = rand(10000, 99999);
    $width = 150; 
    $height = 60;
    $image = imagecreatetruecolor($width, $height);

    $white = imagecolorallocate($image, 255, 255, 255);
    $black = imagecolorallocate($image, 0, 0, 0);
    $gray = imagecolorallocate($image, 200, 200, 200);
    
    imagefilledrectangle($image, 0, 0, $width, $height, $white);

    for ($i = 0; $i < 25; $i++) {
        imageline($image, rand(0, $width), rand(0, $height), rand(0, $width), rand(0, $height), $gray);
    }
    
    for ($i = 0; $i < 1000; $i++) {
        imagesetpixel($image, rand(0, $width), rand(0, $height), $gray);
    }

    $font_size = 5; 
    $text_width = imagefontwidth($font_size) * strlen($code);
    $x = ($width - $text_width) / 2;
    $y = ($height - imagefontheight($font_size)) / 2;

    imagestring($image, $font_size, $x, $y, $code, $black);

    $filename = "captcha_{$chat_id}_" . uniqid() . ".png";
    imagepng($image, $filename);
    imagedestroy($image);

    $url = "https://api.telegram.org/bot$bot_token/sendPhoto";
    $post_fields = [
        'chat_id' => $chat_id,
        'photo' => new CURLFile(realpath($filename)),
        'caption' => "ئەو کۆدە بنووسە کە لە وێنەکەدایە"
    ];

    $ch = curl_init(); 
    curl_setopt($ch, CURLOPT_HTTPHEADER, ["Content-Type:multipart/form-data"]);
    curl_setopt($ch, CURLOPT_URL, $url); 
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1); 
    curl_setopt($ch, CURLOPT_POSTFIELDS, $post_fields); 
    $output = curl_exec($ch);
    curl_close($ch);
    unlink($filename);
    return ['code' => $code, 'response' => $output];
}

function sendEmojiCaptcha($chat_id) {
    $animals = [
        "🐶" => "سەگ", "🐱" => "پشیلە", "🐭" => "میشک", "🐹" => "هامستەر",
        "🐰" => "کەروێشک", "🦊" => "ڕێوی", "🐻" => "ورچ", "🐼" => "پاندا",
        "🐯" => "پڵنگ", "🦁" => "شێر", "🐨" => "کوالا", "🐮" => "گا"
    ];
    
    $keys = array_keys($animals);
    shuffle($keys);

    $correct = $keys[0]; 
    $choices = array_slice($keys, 0, 9); 
    shuffle($choices);

    $keyboard = array_chunk(array_map(function($e) {
        return ["text" => $e, "callback_data" => "EMOJI_VERIF_$e"];
    }, $choices), 3);

    bot('sendMessage', [
        'chat_id' => $chat_id,
        'text' => "🚨 *پێویستە پێش بەکارهێنانی بۆت خۆت پشتڕاست بکەیتەوە!*\n• ئاژەڵی ڕاست هەڵبژێرە لە لیستەکەی خوارەوە!\n• ئاژەڵی داواکراو: $correct",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode(['inline_keyboard' => $keyboard])
    ]);
    return ['code' => $correct];
}

function beroencode($id){
    $g = [1,2,3,4,5,6,7,8,9,0];
    $x = ['A','b','B','C','D','y','o','t','X','Q','K','M'];
    return str_replace($g,$x,$id);
}

function berodecode($id){
    $g = [1,2,3,4,5,6,7,8,9,0];
    $x = ['A','b','B','C','D','y','o','t','X','Q','K','M'];
    return str_replace($x,$g,$id);
}

function coderandom($length = 32) {
    $characters = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
    $charactersLength = strlen($characters);
    $randomString = '';
    for ($i = 0; $i < $length; $i++) {
        $randomString .= $characters[rand(0, $charactersLength - 1)];
    }
    return $randomString;
}

function X_neW($channel, $user_id) {
    $response = bot('getChatMember', [
        'chat_id' => $channel,
        'user_id' => $user_id,
    ]);
    if ($response->ok) {
        $status = $response->result->status;
        return in_array($status, ['member', 'administrator', 'creator']);
    }
    return false;
}

$update = json_decode(file_get_contents('php://input'));
if(isset($update->pre_checkout_query)){
    $id_query = $update->pre_checkout_query->id;
    bot('answerPreCheckoutQuery',[
        'pre_checkout_query_id' => $id_query,
        'ok' => true
    ]);
    exit;
}
if (isset($update->message)) {
    $message = $update->message;
    $message_id = $message->message_id;
    $username = $message->from->username ?? null;
    $chat_id = $message->chat->id;
    $title = $message->chat->title ?? null;
    $text = $message->text ?? null;
    $user = $message->from->username ?? null;
    $name = $message->from->first_name;
    $from_id = $message->from->id;
    $chat_type = $message->chat->type;
} elseif (isset($update->callback_query)) {
    $data = $update->callback_query->data;
    $chat_id = $update->callback_query->message->chat->id;
    $title = $update->callback_query->message->chat->title ?? null;
    $message_id = $update->callback_query->message->message_id;
    $name = $update->callback_query->message->chat->first_name;
    $user = $update->callback_query->message->chat->username ?? null;
    $from_id = $update->callback_query->from->id;
    $chat_type = $update->callback_query->message->chat->type;
}

if (isset($chat_type) && $chat_type != 'private') {
    exit;
}

if(isset($update->my_chat_member) && $update->my_chat_member->new_chat_member->status == 'administrator'){
    if(isset($update->my_chat_member->new_chat_member->user->username) && $update->my_chat_member->new_chat_member->user->username == $USRBOT){
        $chat_id_admin = $update->my_chat_member->chat->id;
        $UU = bot('exportChatInviteLink', ['chat_id' => $chat_id_admin]);

        if($UU && $UU->ok){
            $inviteLink = $UU->result;
        } else {
            $inviteLink = 'بەستەر دەرنەهێنرا ❌';
        }
        
        $from_user_username = $update->my_chat_member->from->username ?? 'N/A';
        
        bot('SendMessage', [
            'chat_id' => $ADMIN,
            'text' => "*- بۆت کرایە ئەدمین لە یەکێک لە کەناڵەکان ➕*\n".
                      "♦️ ئایدی کەناڵ : `". $chat_id_admin."`\n".
                      "🔺 ناوی کەناڵ : *". $update->my_chat_member->chat->title."*\n\n".
                      "*🔜 زانیاری ئەو کەسەی بۆتەکەی زیاد کردووە *\n".
                      "◻️ ناو : *". $update->my_chat_member->from->first_name ."*\n".
                      "▫️یوزەر : [@".$from_user_username."]\n".
                      "◽️ئایدی : `".$update->my_chat_member->from->id."`\n".
                      "◼️ بەستەری دەرهێنراو : ". $inviteLink ."",
            'parse_mode' => 'Markdown',
        ]);
    }
}

if (isset($from_id)) {
    $BLOCKSx = $bot->get("blocks") ?? [];
    if (in_array($from_id, $BLOCKSx)) {
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*- تۆ بلۆک کراویت لە بەکارهێنانی بۆت ⛔️*",
            'parse_mode' => 'Markdown',
        ]);
        return;
    }
}

if($text and $sessions->get('mode_' . $from_id) == 'CONTACT_MODE'){
    $btn_name = $sessions->get('contact_btn_name_' . $from_id);
    $reply_text = $bot->get("zrs_contact_reply_$btn_name") ?? "پەیامەکەت گەیشت، بەزوترین کات وەڵامت دەدرێتەوە.";
    
    $user_tag = $username ? "@$username" : "نییە";

    bot('SendMessage', [
        'chat_id' => $ADMIN,
        'text' => "📩 *نامەیەکی نوێ لە بەشی پەیوەندی دوگمەی:* ($btn_name)\n\n👤 *زانیاری نێرەر:*\n▪️ ناو: [$name](tg://user?id=$from_id)\n▪️ یوزەر: $user_tag\n▪️ ئایدی: `$from_id`\n\n📝 *ناوەڕۆکی پەیام:*\n$text",
        'parse_mode' => 'Markdown',
    ]);

    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => $reply_text,
        'parse_mode' => 'Markdown',
        'reply_to_message_id' => $message_id,
    ]);

    $sessions->delete('mode_' . $from_id);
    $sessions->delete('contact_btn_name_' . $from_id);
    return;
}

$name_text = $bot->get('name_bot') ?? "Your Support";
$a3ml = $bot->get('amla_text') ?? "خاڵ";
$current_coins = $wallets->get('coins_'.$chat_id) ?? 0;

$START = "
<b>بەخێربێیت بۆ بۆتی $name_text <tg-emoji emoji-id='5472055112702629499'>👋</tg-emoji></b>

<b><tg-emoji emoji-id='5375296873982604963'>💰</tg-emoji> باڵانسی تۆ : #COINS ".$a3ml." </b>
<b><tg-emoji emoji-id='5422683699130933153'>🪪</tg-emoji> ئایدی تۆ : <code>#MY_ID</code> </b>
";

$NOW_STA = $bot->get('START_');

$u_handle = $username ?? $user ?? null;
$user_tag = $u_handle ? "@$u_handle" : "نییە";

if($NOW_STA){
    $name_link = "[$name](tg://user?id=$from_id)";    
    $START = str_replace(
        ['#a',       '#b',  '#c',      '#d',      '#e'], 
        [$name_link, $name, $from_id, $user_tag,  $current_coins], 
        $NOW_STA
    );
}

$START = str_replace(['#COINS', '#MY_ID'], [$current_coins, $from_id], $START);
$START = preg_replace('/\*(.*?)\*/', '<b>$1</b>', $START);
$START = preg_replace('/_(.*?)_/', '<i>$1</i>', $START);
$START = preg_replace('/`(.*?)`/', '<code>$1</code>', $START);
$START = preg_replace('/\[(.*?)\]\((.*?)\)/', '<a href="$2">$1</a>', $START);


$admins_from_db = $bot->get("admins") ?? [];
$ADMINS = array_map('intval', $admins_from_db);
$ADMINS[] = ADMIN;
$ADMINS = array_unique($ADMINS);


if(!$bot->get('zrar_alasase')){
$bot->set('zrar_alasase' , '✅');
} 

if(in_array($chat_id, $ADMINS)) {

if(!$bot->get('HIMAIA_restriction')){
    $bot->set('HIMAIA_restriction' , '❌');
}
if(!$bot->get('HIMAIA_restriction_media')){
    $bot->set('HIMAIA_restriction_media' , '❌');
}
if(!$bot->get('HIMAIA_restriction_LINK')){
    $bot->set('HIMAIA_restriction_LINK' , '❌');
}
if(!$bot->get('HIMAIA_restriction_text')){
    $bot->set('HIMAIA_restriction_text' , '❌');
}
      


if($update->message->reply_to_message->reply_markup->inline_keyboard and $text == "پیشاندانی دوگمەکان"){
foreach($update->message->reply_to_message->reply_markup->inline_keyboard as $y){
    foreach($y as $y){
        $TEX = $y->text;
       $call = $y->callback_data;
for ($i = 0; $i < 3; $i++) {
    $call = base64_encode($call);
}

        $T = $T."*دوگمە:* `$TEX` - *کۆدی دوگمە:* `BB:$call` \n";
    }
}
bot('SendMessage', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "$T",
        'parse_mode' => 'Markdown',
    ]);
}
    if($data == "GOTO_ADMIN_PANEL"){
    if(!$bot->get('generals_siana')){
        $bot->set('generals_siana' , '❌');
    }
    if(!$bot->get('generals_entry')){
        $bot->set('generals_entry' , '✅');
    }
    if(!$bot->get('generals_tmoil')){
        $bot->set('generals_tmoil' , '✅');
    }
    if(!$bot->get('HIMAIA_JIHAT_ITSAL')){
        $bot->set('HIMAIA_JIHAT_ITSAL' , '❌');
    }
    if(!$bot->get('HIMAIA_THQQ_BSRY')){
        $bot->set('HIMAIA_THQQ_BSRY' , '❌');
    }
    if(!$bot->get('HIMAIA_passworder')){
        $bot->set('HIMAIA_passworder' , 'ناچالاک ❌');
    }
    if(!$bot->get('HIMAIA_LIN_KER')){
        $bot->set('HIMAIA_LIN_KER' , 'ناچالاک ❌');
    }
    if(!$bot->get('HIMAIA_notifa')){
        $bot->set('HIMAIA_notifa' , '✅');
    }
    if(!$bot->get('AL_NJOM_x')){
        $bot->set('AL_NJOM_x' , '❌');
    }
    if(!$bot->get('al3qobat')){
        $bot->set('al3qobat' , 'ناچالاک ❌');
    }

    bot('EditMessageText', [
    'chat_id' => $chat_id,
    'message_id' => $message_id,
    'text' => "~ بەخێربێیت بۆ پانێڵی ئەدمینی بۆت 🤖
~ دەتوانیت هەموو فەرمانەکانی بۆت لەم بەشە کۆنترۆڵ بکەیت",
    'parse_mode' => 'Markdown', 
    'reply_markup' => json_encode([
        'inline_keyboard' => [
            [["text" => "چاکسازی : ".$bot->get('generals_siana'), "callback_data" => "tgle_siana"],
["text" => "ئاگاداری هاتن : ".$bot->get('generals_entry'), "callback_data" => "tgle_entry"]],
            [["text" => "نامەی بەخێرهاتن ( /start )", "callback_data" => "al_START"]],
            [["text" => "پاراستنی بۆت", "callback_data" => "ALHMAIA"],["text" => "بلۆککردن", "callback_data" => "BLOCKS"]],
            [["text" => "دوگمە شەفافەکان", "callback_data" => "AL_AZRAR"],
            ["text" => "فەرمانە کورتکراوەکان", "callback_data" => "al_commands"]],
            [["text" => "جۆینی ناچاری", "callback_data" => "shtrak_jbare"],
["text" => "ناردنی گشتی", "callback_data" => "broadcast"]],
[["text" => "ئامارەکان", "callback_data" => "ADMIN_STATS"],
['text' => 'ئەدمینەکان', 'callback_data' => 'ADMINS']],
            [["text" => "ڕێکخستنەکانی بۆت", "callback_data" => "SETTINGER"]],
            [["text" => "گەڕانەوە بۆ دۆخی بەکارهێنەر", "callback_data" => "BACK"]],            
        ]
    ])
]);
$sessions->delete('mode_'.$from_id);
return; 
}

if(substr($data, 0, 8) == "DEL_CMD:"){
    $cmd = str_replace("DEL_CMD:", "", $data);

    $cmd_list = $bot->get('cmd_list') ?: [];
    $new_list = array_filter($cmd_list, fn($c) => $c !== $cmd);
    $bot->set('cmd_list', array_values($new_list));

    $bot->delete("cmd_" . $cmd);

    bot('answerCallbackQuery', [
        'callback_query_id' => $update->callback_query->id,
        'text' => "فەرمانی $cmd سڕایەوە",
        'show_alert' => false
    ]);

    $data = 'al_commands'; 
}


if($data == 'al_commands'){
    $cmd_list = $bot->get('cmd_list') ?: [];
    $buttons = [];

    foreach(array_reverse($cmd_list) as $cmd){
        $desc = $bot->get('cmd_' . $cmd);
        $buttons[] = [
            ["text" => "$cmd - $desc", "callback_data" => "none"],
            ["text" => "❌", "callback_data" => "DEL_CMD:$cmd"]
        ];
    }

    $buttons[] = [["text" => "➕ زیادکردنی فەرمان", "callback_data" => "ADD_ADMR"]];
    $buttons[] = [["text" => "بەشی وەڵامدانەوەکان", "callback_data" => "QSM_ALRDOD"]];
    $buttons[] = [["text" => "↩️ گەڕانەوە", "callback_data" => "BACKADMIN"]];

    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- بەشی فەرمانە کورتکراوەکان*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode(['inline_keyboard' => $buttons])
    ]);
    $sessions->delete('mode_' . $from_id);
}
if ($data == "TOGGLE_REPLIES") {
    $status = $auto_replies->get("replies_enabled") ?: "on";
    $new = ($status == "on") ? "off" : "on";
    $auto_replies->set("replies_enabled", $new);
    bot('answerCallbackQuery', ['callback_query_id' => $update->callback_query->id, 'text' => "وەڵامدانەوە " . ($new == "on" ? "چالاک کرا" : "ناچالاک کرا"), 'show_alert' => false]);
    $data = "QSM_ALRDOD";
}

if ($data == "TOGGLE_SENSITIVITY") {
    $current = $auto_replies->get("sensitivity") ?: "strict";
    $new = ($current == "strict") ? "loose" : "strict";
    $auto_replies->set("sensitivity", $new);
    bot('answerCallbackQuery', ['callback_query_id' => $update->callback_query->id, 'text' => "هەستیاری گۆڕدرا بۆ " . ($new == "strict" ? "تەواو" : "بەشێک"), 'show_alert' => false]);
    $data = "QSM_ALRDOD";
}
if (strpos($data, "DEL_REPLY:") === 0) {
    $word = explode(":", $data)[1];
    $auto_replies->delete("reply_$word");

    $words = explode(",", $auto_replies->get("reply_words") ?: "");
    $words = array_filter($words, fn($w) => $w !== $word);
    $auto_replies->set("reply_words", implode(",", $words));

    bot('answerCallbackQuery', [
        'callback_query_id' => $update->callback_query->id,
        'text' => "وەڵام بۆ [$word] سڕایەوە",
        'show_alert' => false
    ]);
    $data = "LIST_REPLIES";
}

if ($data == "QSM_ALRDOD") {
    $status = $auto_replies->get("replies_enabled") ?: "on";
    $sensitivity = $auto_replies->get("sensitivity") ?: "strict";

    $buttons = [
        [["text" => "زیادکردنی وەڵامی نوێ", "callback_data" => "ADD_REPLY"]],
        [["text" => "پیشاندانی هەموو وەڵامەکان", "callback_data" => "LIST_REPLIES"]],
        [["text" => ($status == "on" ? "ناچالاککردنی وەڵامی ئۆتۆماتیکی" : "چالاککردنی وەڵامی ئۆتۆماتیکی"), "callback_data" => "TOGGLE_REPLIES"]],
        [["text" => ($sensitivity == "strict" ? "هەستیاری: تەواو (هاوتا)" : "هەستیاری: بەشێک (لەخۆدەگرێت)"), "callback_data" => "TOGGLE_SENSITIVITY"]],
        [["text" => "گەڕانەوە بۆ لیست", "callback_data" => "al_commands"]]
    ];

    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*ڕێکخستنی وەڵامدانەوەی ئۆتۆماتیکی:*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode(['inline_keyboard' => $buttons])
    ]);
    $sessions->delete("mode_$from_id");
    return;
}

if ($data == "LIST_REPLIES") {
    $words = explode(",", $auto_replies->get("reply_words") ?: "");
    $buttons = [];

    foreach ($words as $word) {
        if ($word == "") continue;
        $buttons[] = [["text" => "🗑 سڕینەوەی [$word]", "callback_data" => "DEL_REPLY:$word"]];
    }

    if (empty($buttons)) {
        $buttons[] = [["text" => "هیچ وەڵامێک نییە", "callback_data" => "none"]];
    }

    $buttons[] = [["text" => "گەڕانەوە", "callback_data" => "QSM_ALRDOD"]];

    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*لیستی وەڵامەکان:*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode(['inline_keyboard' => $buttons])
    ]);
    return;
}

if ($data == "ADD_REPLY") {
    $sessions->set("mode_$from_id", "add_reply_word");
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*ئەو وشەیە بنێرە کە دەتەوێت وەڵامی بۆ دابنێیت:*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode(['inline_keyboard' => [
            [["text" => "گەڕانەوە", "callback_data" => "QSM_ALRDOD"]]
        ]])
    ]);
    return;
}

// استلام الكلمة التي سيتم ربطها برد تلقائي
if ($sessions->get("mode_$from_id") == "add_reply_word") {
    $auto_replies->set("tmp_word_$from_id", $text);
    $sessions->set("mode_$from_id", "add_reply_text");
    bot('sendMessage', [
        'chat_id' => $chat_id,
        'text' => "*ئێستا وەڵامەکە بنێرە بۆ وشەی:* `$text`",
        'parse_mode' => 'Markdown'
    ]);
    return;
}

// استلام الرد المرتبط بالكلمة وتخزينه
if ($sessions->get("mode_$from_id") == "add_reply_text") {
    $word = $auto_replies->get("tmp_word_$from_id");
    $auto_replies->set("reply_$word", $text);
    $auto_replies->delete("tmp_word_$from_id");

    $words = explode(",", $auto_replies->get("reply_words") ?: "");
    if (!in_array($word, $words)) {
        $words[] = $word;
        $auto_replies->set("reply_words", implode(",", $words));
    }

    $sessions->delete("mode_$from_id");
    bot('sendMessage', [
        'chat_id' => $chat_id,
        'text' => "*وەڵامەکە بۆ وشەی:* `$word` *پاشەکەوت کرا*",
        'parse_mode' => 'Markdown'
    ]);
    return;
}


if($data == 'ADD_ADMR'){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- فەرمانەکە بەم شێوەیە بنێرە*
start - دەستپێکردنی بەکارهێنان",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "al_commands"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, $data);
    return;
}
if($text and $sessions->get('mode_' . $from_id) == 'ADD_ADMR'){
    $G = explode(' - ' , $text);
    if($G[0] and $G[1]){
        $cmd_list = $bot->get('cmd_list') ?: [];
        if (!in_array($G[0], $cmd_list)) {
            $cmd_list[] = $G[0];
            $bot->set('cmd_list', $cmd_list);
        }

        $bot->set('cmd_' . $G[0], $G[1]);
        $sessions->delete('mode_' . $from_id);

        bot('sendMessage', [
            'chat_id' => $chat_id,
            'parse_mode' => 'Markdown',
            'text' => "• فەرمانی '". $G[0]."' بە وەسفی '". $G[1] ."' زیادکرا.",
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "گەڕانەوە", "callback_data" => "al_commands"]],
                ]
            ])
        ]);
    }else{
        bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'text' => "• شێوازەکە هەڵەیە، تکایە دڵنیابەرەوە لە مەرجەکان! .",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "al_commands"]],
            ]
        ])
    ]);
    }
    return;
}

if(!$bot->get('HIMAIA_EMOJI_CHECK')){
    $bot->set('HIMAIA_EMOJI_CHECK', '❌');
}


$OPOF_ = explode('OPOF_' , $data)[1];
if($OPOF_){
    $NOWLY = $bot->get('HIMAIA_' . $OPOF_);
    if($OPOF_ == 'JIHAT_ITSAL' or $OPOF_ == 'THQQ_BSRY' or $OPOF_ == 'EMOJI_CHECK' or $OPOF_ == 'notifa'){
    if($NOWLY == '✅'){
        $SETto= '❌';
    }else{
         $SETto= '✅';
    }
    $bot->set('HIMAIA_' . $OPOF_ , $SETto);
    $data = "ALHMAIA";

    }elseif($OPOF_ == "passworder" or $OPOF_ == "LIN_KER"){
        if($OPOF_ == 'passworder'){
            $LINKER = $bot->get('HIMAIA_LIN_KER');
            if($LINKER == 'چالاک ✅'){
                bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "تایبەتمەندی پاراستن بە بەستەر چالاک بوو، ناچالاک کرا و گۆڕدرا بۆ کۆدی نهێنی .",
        'show_alert' => true,
    ]);
    $bot->set('HIMAIA_LIN_KER' , "ناچالاک ❌");
            }
        }
        if($OPOF_ == 'LIN_KER'){
            $passworder = $bot->get('HIMAIA_passworder');
            if($passworder == 'چالاک ✅'){
                bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "تایبەتمەندی پاراستن بە کۆدی نهێنی چالاک بوو، ناچالاک کرا و گۆڕدرا بۆ بەستەر .",
        'show_alert' => true,
    ]);
    $bot->set('HIMAIA_passworder' , "ناچالاک ❌");
            }
        }
        if($NOWLY == 'چالاک ✅'){
            $SETto= 'ناچالاک ❌';
        }else{
             $SETto= 'چالاک ✅';
        }
        $bot->set('HIMAIA_' . $OPOF_ , $SETto);
        $data = $OPOF_;
    }elseif(preg_match("/restriction/",$OPOF_)){
        if($NOWLY == '✅'){
            $SETto= '❌';
        }else{
             $SETto= '✅';
        }
        $bot->set('HIMAIA_' . $OPOF_ , $SETto);
        $data = "HMAIA_ALMHTWA";
    }
    
}
if($data == "DEL_ALL_ALOWER"){
    $Y = 0;
    foreach($security->get("ALLOWS") as $G){
        $Y =+ 1;
        $security->delete("I_UER_$G");
        $security->delete("I_UER2_$G");
        $security->delete("I_UER3_$G");
    }
    bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "ژمارەی $Y کەس لە ڕێگەپێدراوان سڕانەوە ,",
        'show_alert' => true,
    ]);
     $security->delete("ALLOWS");
    $data = "ALHMAIA";
}
if($data == "ALHMAIA"){
    $ALMSMOHEN = count($security->get("ALLOWS"));
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- بەشی پاراستنی بۆت*
- ژمارەی ڕێگەپێدراوان لەڕێگەی بژاردەکانی پاراستن : *$ALMSMOHEN*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "ئاگادارییەکان : " . $bot->get('HIMAIA_notifa'), "callback_data" => "OPOF_notifa"]],
                [["text" => "سڕینەوەی هەموو ڕێگەپێدراوان", "callback_data" => "DEL_ALL_ALOWER"]],
                [["text" => "قوفڵکردنی بۆت بە کۆدی چوونەژوورەوە", "callback_data" => "passworder"]],
                [["text" => "قوفڵکردنی بۆت بە بەستەری چوونەژوورەوە", "callback_data" => "LIN_KER"]],
                [["text" => "داواکردنی پەیوەندییەکان (Contact)", "callback_data" => "OPOF_JIHAT_ITSAL"],["text" => $bot->get('HIMAIA_JIHAT_ITSAL'), "callback_data" => "OPOF_JIHAT_ITSAL"]],
                [["text" => "پشکنینی بینایی", "callback_data" => "OPOF_THQQ_BSRY"],["text" => $bot->get('HIMAIA_THQQ_BSRY'), "callback_data" => "OPOF_THQQ_BSRY"]],
                [["text" => "پشکنین بە ئیمۆجی", "callback_data" => "OPOF_EMOJI_CHECK"],["text" => $bot->get('HIMAIA_EMOJI_CHECK'), "callback_data" => "OPOF_EMOJI_CHECK"]],
                [["text" => "پاراستنی ناوەڕۆکی بۆت", "callback_data" => "HMAIA_ALMHTWA"]],
                [["text" => "گەڕانەوە", "callback_data" => "BACKADMIN"]],
            ]
        ])
    ]);
}


if($data == "HMAIA_ALMHTWA"){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*• بەخێربێیت بۆ بەشی پاراستنی ناوەڕۆکی بۆت 🥷🏾*

- دەتوانیت هەموو پەیامەکانی بۆت بپارێزیت لە هەڵگرتن (Save) یان ناردن (Forward) بۆ دەرەوەی بۆت",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "پاراستنی ناوەڕۆکی بۆت : " . $bot->get('HIMAIA_restriction'), "callback_data" => "OPOF_restriction"]],
                [["text" => "جیاکردنەوەی میدیا لە پاراستن : " . $bot->get('HIMAIA_restriction_media'), "callback_data" => "OPOF_restriction_media"]],
                [["text" => "جیاکردنەوەی پەیامە بەستەردارەکان لە پاراستن : " . $bot->get('HIMAIA_restriction_LINK'), "callback_data" => "OPOF_restriction_LINK"]],
                [["text" => "جیاکردنەوەی دەقەکان لە پاراستن : " . $bot->get('HIMAIA_restriction_text'), "callback_data" => "OPOF_restriction_text"]],
                [["text" => "گەڕانەوە", "callback_data" => "ALHMAIA"]],
            ]
        ])
    ]);
}
if($data == "CHANGE_RABT"){
    $security->set('THE_LINK' , coderandom());
    bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "بەستەرەکە گۆڕدرا، بەستەرێکی نوێت دانا .",
        'show_alert' => true,
    ]);
    $data = "LIN_KER";
}

if ($data == "LIN_KER") {
    if (!$security->get('THE_LINK')) {
        $security->set('THE_LINK', coderandom());
    }
    $THE_LINK = $security->get('THE_LINK');

    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- بەشی قوفڵکردنی بۆت بە بەستەری چوونەژوورەوە*\n- بەستەری ئێستا : `https://t.me/$usrbot?start=$THE_LINK` .",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [
                    ["text" => "دۆخ : " . $bot->get('HIMAIA_LIN_KER'), "callback_data" => "OPOF_LIN_KER"]
                ],
                [
                    ["text" => "گۆڕینی بەستەر", "callback_data" => "CHANGE_RABT"]
                ],
                [
                    ["text" => "گەڕانەوە", "callback_data" => "BACKADMIN"]
                ]
            ]
        ])
    ]);
}

if($data == "passworder"){
    $THE_RMZ = $bot->get('HRMZAR_RMZ') ?? 'نییە';
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- بەشی قوفڵکردنی بۆت بە کۆدی چوونەژوورەوە*
- کۆدی ئێستا : `$THE_RMZ` .

*- ئاگاداری* : لەکاتی دانانی هەر کۆدێکی نوێ، داوا لە بەکارهێنەران دەکرێت کۆدەکە دووبارە بنووسنەوە",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "دۆخ : " . $bot->get('HIMAIA_passworder'), "callback_data" => "OPOF_passworder"]],
                [["text" => "دانانی کۆد", "callback_data" => "RMZAR_RMZ"]],
                [["text" => "گەڕانەوە", "callback_data" => "BACKADMIN"]],
            ]
        ])
    ]);
}

if($data == "RMZAR_RMZ"){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- کۆدی نهێنی بنێرە بۆ دانانی :*
- دەتوانیت پیت و ژمارە بەکاربهێنیت .",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [

                [["text" => "گەڕانەوە", "callback_data" => "passworder"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, $data);
    return;
}

if($text and $sessions->get('mode_' . $from_id) == 'RMZAR_RMZ'){
    bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'text' => "• کۆدی '$text' دانرا .",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "passworder"]],
            ]
        ])
    ]);
     $bot->set('HRMZAR_RMZ' , $text);
    $sessions->delete('mode_' . $from_id);
}

$tOgal_ = explode('tOgal_' , $data)[1];
if($tOgal_){
    $JJ = $bot->get('shi3ar_' . $tOgal_);
    if($JJ == '❌'){
        $Y = '✅';
    }else{
        $Y = '❌';
    }
     $bot->set('shi3ar_' . $tOgal_ ,$Y );
     $data = 'SETTINGER';
}
if($data == "SETTINGER"){
    $ish3ar_tlbat = $bot->get('shi3ar_tlbat') ?? '✅';
    $ish3ar_tmoil = $bot->get('shi3ar_tmoil') ?? '✅';
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*✨ سەنتەری ڕێکخستنە گشتییەکان*
هەموو تواناکانی بۆت لە ژێر دەستتدان",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
    [
        ['text' => "ئاگاداری داواکاری : $ish3ar_tlbat", 'callback_data' => 'tOgal_tlbat'],
        ['text' => "ئاگاداری ئەندام : $ish3ar_tmoil", 'callback_data' => 'tOgal_tmoil']
    ],
    [
        ['text' => "زیادکردنی $a3ml", 'callback_data' => 'addcoins'],
        ['text' => "کەمکردنەوەی $a3ml", 'callback_data' => 'removecoins']
    ],
    [
        ['text' => "پشکنینی $a3ml", 'callback_data' => 'kshfnqat'],
        ['text' => "پشکنینی داواکاری", 'callback_data' => 'admin_check_order']
    ],
    [
        ['text' => "ناردنی $a3ml بۆ هەمووان", 'callback_data' => 'NQAT_TO_ALL'],
        ['text' => "سڕینەوەی $a3ml هەمووان", 'callback_data' => 'DELETE_ALL_NQAT']
    ],
    [
        ['text' => "پاڵاوتنی $a3ml", 'callback_data' => 'TSFIA_NQT'],
        ['text' => 'دۆخی سایت', 'callback_data' => 'site_info'],
    ],
    [
        ['text' => 'دروستکردنی کۆدی دیاری', 'callback_data' => 'make_hdia'],
        ['text' => 'دروستکردنی بەستەری دیاری', 'callback_data' => 'makelinkhdia']
    ],
    [
        ['text' => 'بەستنەوەی API دەرەکی', 'callback_data' => 'asasse'],
        ['text' => 'دەستکاریکردنی دەقەکان', 'callback_data' => 'alta3en']
    ],
    [
        ['text' => 'سزاکانی ئەندام', 'callback_data' => 'al_3qboat'],
        ['text' => 'کۆنترۆڵی ئەندام', 'callback_data' => 'funding_management']
    ],
    [
        ['text' => 'وکیلەکان', 'callback_data' => 'AGENTS']
    ],
    [
        ['text' => 'کڕینی ئۆتۆماتیکی', 'callback_data' => 'AL_SH7n'],
        ['text' => 'نوسخەی یەدەگ', 'callback_data' => 'the_backup']
    ],
    [
        ['text' => 'خزمەتگوزاری و بەشەکان', 'callback_data' => 'xdmats']
],
    [['text' => 'گەڕانەوە', 'callback_data' => 'BACKADMIN']],
]
        ])
    ]);
}

if($data == 'admin_check_order'){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*🆔 ئایدی داواکاری بنێرە بۆ وەرگرتنی زانیاری تەواو:*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "SETTINGER"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, 'admin_chk_ord');
}

if($text && $sessions->get('mode_' . $from_id) == 'admin_chk_ord'){
    $order_id = trim($text);
    $order_data = $orders->get($order_id);
    
    if($order_data){
        $split = explode('|', $order_data);
        $API = $split[0] ?? 'N/A';
        $DOMIN = $split[1] ?? 'N/A';
        $service_name = $split[2] ?? 'N/A';
        $link = $split[3] ?? 'N/A';
        $quantity = $split[4] ?? '0';
        $price = $split[5] ?? '0';
        $user_id_ord = $split[6] ?? '0';

        $user_name_ord = $users->get($user_id_ord) ?? "نەناسراو";

        $api_url = "https://$DOMIN/api/v2?key=$API&action=status&order=$order_id";
        $api_res = @file_get_contents($api_url);
        $api_json = json_decode($api_res, true);

        $status = $api_json['status'] ?? "تۆمارنەکراوە";
        
        $start_count = $api_json['start_count'] ?? "0";
        if($start_count === "" || $start_count === null) {
            $start_count = "0";
        }

        $remains = $api_json['remains'] ?? "0";

        $status_map = [
            'Pending' => 'لە چاوەڕوانی 🕒',
            'Processing' => 'لە جێبەجێکردن ⚙️',
            'In progress' => 'بەرەوپێشچوون 🚀',
            'Completed' => 'تەواوبوو ✅',
            'Partial' => 'بەشێکی تەواو ⚠️',
            'Canceled' => 'هەڵوەشایەوە ❌',
            'Fail' => 'شکست 🚫'
        ];
        $status_display = $status_map[$status] ?? $status;

        $msg = "📋 *وردەکاری تەواوی داواکاری*

📇 *ژمارەی داواکاری:* `$order_id`
👤 *خاوەن داواکاری:* [$user_name_ord](tg://user?id=$user_id_ord)
🔢 *ئایدی بەکارهێنەر:* `$user_id_ord`
🛠 *خزمەتگوزاری:* `$service_name`
🔗 *بەستەر:* `$link`
📊 *دۆخی ئێستا:* $status_display
📉 *ژمارەی داواکراو:* `$quantity`
🏁 *ژمارەی سەرەتا:* `$start_count`
⏳ *ژمارەی ماوە:* `$remains`
💰 *تێچوو لە بۆت:* `$price $a3ml`
";

        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => $msg,
            'parse_mode' => 'Markdown',
            'disable_web_page_preview' => true,
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "🔙 گەڕانەوە", "callback_data" => "SETTINGER"]],
                ]
            ])
        ]);
        $sessions->delete('mode_' . $from_id);

    } else {
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "❌ *ئەم داواکارییە لە داتابەیس بوونی نییە!*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "🔙 گەڕانەوە", "callback_data" => "SETTINGER"]],
                ]
            ])
        ]);
    }
}

if($data == "funding_management"){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- بەشی کۆنترۆڵی ئەندام ⚙️*\n\nکردارێک هەڵبژێرە:",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [['text' => "🚫 بلۆککردنی کەناڵێک لە ئەندام", 'callback_data' => "block_funding_channel"]],
                [['text' => "✅ لابردنی بلۆکی کەناڵ", 'callback_data' => "unblock_funding_channel"]],
                [['text' => "🗑️ هەڵوەشاندنەوەی ئەندامی ئێستا", 'callback_data' => "cancel_current_funding"]],
                [['text' => "🔙 گەڕانەوە", 'callback_data' => "SETTINGER"]],
            ]
        ])
    ]);
    $sessions->delete('mode_' . $from_id);
}

if ($data == 'block_funding_channel') {
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- یوزەری ئەو کەناڵە بنێرە کە دەتەوێت بلۆکی بکەیت لە ئەندام*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [['text' => "🔙 گەڕانەوە", 'callback_data' => "funding_management"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, 'set_block_channel');
}

if ($text and $sessions->get('mode_' . $from_id) == 'set_block_channel') {
    if (preg_match('/^@[\w_]{5,}$/', $text)) {
        $channel_to_block = strtolower($text);
        $blocklist = $bot->get('funding_blocklist') ?? [];

        if (!in_array($channel_to_block, $blocklist)) {
            $blocklist[] = $channel_to_block;
            $bot->set('funding_blocklist', $blocklist);
        }

        $funding_id_to_cancel = null;
        $all_funding_ids_raw = $funding->get("IDXS");
        if ($all_funding_ids_raw) {
            $all_funding_ids = explode("\n", trim($all_funding_ids_raw));
            foreach ($all_funding_ids as $id) {
                if (empty(trim($id))) continue;
                $infos = $funding->get('INFOS_' . $id);
                if ($infos) {
                    $channel_in_db = explode('|', $infos)[2] ?? null;
                    if ($channel_in_db && strtolower($channel_in_db) == $channel_to_block) {
                        $funding_id_to_cancel = $id;
                        break;
                    }
                }
            }
        }

        $cancellation_message = "";
        if ($funding_id_to_cancel) {
            $INFOS = $funding->get('INFOS_' . $funding_id_to_cancel);
            list($COUNT, $PRICE_TMOIL, $CHANNEL, $OWNER) = array_pad(explode('|', $INFOS), 4, 'N/A');
            $MID = $funding->get("MID_$funding_id_to_cancel");

            $SVT = str_replace($funding_id_to_cancel, '', $funding->get("IDXS"));
            $funding->set("IDXS", $SVT);
            $CVT = str_replace($funding_id_to_cancel, '', $funding->get("IDXS_$OWNER"));
            $funding->set("IDXS_$OWNER", $CVT);

            $funding->delete('INFOS_' . $funding_id_to_cancel);
            $funding->delete('TMOIL_FOR_' . $CHANNEL);
            $funding->delete("MID_$funding_id_to_cancel");
            $funding->delete("NOW_PRGRESS_" . $funding_id_to_cancel);

            if ($OWNER && $MID) {
                bot('editMessageReplyMarkup', [
                    'chat_id' => $OWNER,
                    'message_id' => $MID,
                    'reply_markup' => json_encode(['inline_keyboard' => [[["text" => "ئەندامەکەت لەلایەن بەڕێوەبەرایەتییەوە هەڵوەشێندرایەوە", "url" => "tg://user?id=$ADMIN"]]]])
                ]);
            }
            $cancellation_message = "\n- ئەندامی چالاکی ئەم کەناڵە هەڵوەشێندرایەوە.";
        }

        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => "✅ *کەناڵی* `$channel_to_block` *بە سەرکەوتوویی بلۆک کرا.*".$cancellation_message,
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode(['inline_keyboard' => [[['text' => "🔙 گەڕانەوە", 'callback_data' => "funding_management"]]]])
        ]);
        $sessions->delete('mode_' . $from_id);

    } else {
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => "*❗️فۆرمات هەڵەیە. تکایە یوزەری کەناڵ بنێرە کە بە @ دەست پێبکات*",
            'parse_mode' => 'Markdown'
        ]);
    }
}

if ($data == 'unblock_funding_channel') {
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- یوزەری ئەو کەناڵە بنێرە کە دەتەوێت بلۆکەکەی لابدەیت*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [['text' => "🔙 گەڕانەوە", 'callback_data' => "funding_management"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, 'set_unblock_channel');
}

if ($text and $sessions->get('mode_' . $from_id) == 'set_unblock_channel') {
    if (preg_match('/^@[\w_]{5,}$/', $text)) {
        $channel_to_unblock = strtolower(trim($text));
        $blocklist = $bot->get('funding_blocklist') ?? [];
        $channel_found = false;

        $new_blocklist = [];
        foreach ($blocklist as $blocked_channel) {
            if (strtolower($blocked_channel) == $channel_to_unblock) {
                $channel_found = true;
            } else {
                $new_blocklist[] = $blocked_channel;
            }
        }
        
        if ($channel_found) {
            $bot->set('funding_blocklist', $new_blocklist);
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => "✅ *بلۆکی کەناڵی:* `$text` *بە سەرکەوتوویی لابرا.*",
                'parse_mode' => 'Markdown',
                'reply_markup' => json_encode(['inline_keyboard' => [[['text' => "🔙 گەڕانەوە", 'callback_data' => "funding_management"]]]])
            ]);
        } else {
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => "❗️*ئەم کەناڵە لە بنەڕەتدا بلۆک نییە.*",
                'parse_mode' => 'Markdown'
            ]);
        }
    } else {
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => "*❗️فۆرمات هەڵەیە. تکایە یوزەری کەناڵ بنێرە کە بە @ دەست پێبکات*",
            'parse_mode' => 'Markdown'
        ]);
    }
    $sessions->delete('mode_' . $from_id);
}

if ($data == 'cancel_current_funding') {
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- یوزەری کەناڵ یان ژمارەی ئەندام بنێرە بۆ هەڵوەشاندنەوە*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [['text' => "🔙 گەڕانەوە", 'callback_data' => "funding_management"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, 'set_cancel_funding');
}

if ($text and $sessions->get('mode_' . $from_id) == 'set_cancel_funding') {
    $input = trim($text);
    $funding_id_to_cancel = null;

    if (is_numeric($input)) {
        $funding_id_to_cancel = $input;
    } elseif (preg_match('/^@[\w_]{5,}$/', $input)) {
        $channel_to_find = strtolower($input);
        $all_funding_ids_raw = $funding->get("IDXS");
        if ($all_funding_ids_raw) {
            $all_funding_ids = explode("\n", trim($all_funding_ids_raw));
            foreach ($all_funding_ids as $id) {
                if (empty(trim($id))) continue;
                $infos = $funding->get('INFOS_' . $id);
                if ($infos) {
                    $channel_in_db = explode('|', $infos)[2] ?? null;
                    if ($channel_in_db && strtolower($channel_in_db) == $channel_to_find) {
                        $funding_id_to_cancel = $id;
                        break;
                    }
                }
            }
        }
    }

    if ($funding_id_to_cancel) {
        $INFOS = $funding->get('INFOS_' . $funding_id_to_cancel);
        if ($INFOS) {
            list($COUNT, $PRICE_TMOIL, $CHANNEL, $OWNER) = array_pad(explode('|', $INFOS), 4, 'N/A');
            $MID = $funding->get("MID_$funding_id_to_cancel");

            $SVT = str_replace($funding_id_to_cancel, '', $funding->get("IDXS"));
            $funding->set("IDXS", $SVT);
            $CVT = str_replace($funding_id_to_cancel, '', $funding->get("IDXS_$OWNER"));
            $funding->set("IDXS_$OWNER", $CVT);

            $funding->delete('INFOS_' . $funding_id_to_cancel);
            $funding->delete('TMOIL_FOR_' . $CHANNEL);
            $funding->delete("MID_$funding_id_to_cancel");
            $funding->delete("NOW_PRGRESS_" . $funding_id_to_cancel);

            if ($OWNER && $MID) {
                bot('editMessageReplyMarkup', [
                    'chat_id' => $OWNER,
                    'message_id' => $MID,
                    'reply_markup' => json_encode(['inline_keyboard' => [[["text" => "ئەندامەکەت لەلایەن بەڕێوەبەرایەتییەوە هەڵوەشێندرایەوە", "url" => "tg://user?id=$ADMIN"]]]])
                ]);
            }
            
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => "✅ *ئەندامی ژمارە* `$funding_id_to_cancel` *بۆ کەناڵی* `$CHANNEL` *بە سەرکەوتوویی هەڵوەشێندرایەوە.*",
                'parse_mode' => 'Markdown',
                'reply_markup' => json_encode(['inline_keyboard' => [[['text' => "🔙 گەڕانەوە", 'callback_data' => "funding_management"]]]])
            ]);

        } else {
             bot('sendMessage', [
                 'chat_id' => $chat_id,
                 'text' => "❗️*هیچ ئەندامێک بەم ژمارەیە نەدۆزرایەوە.*",
                 'parse_mode' => 'Markdown'
]);
        }
    } else {
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => "❗️*هیچ ئەندامێکی چالاک بۆ ئەم کەناڵە یان ژمارەیە نەدۆزرایەوە.*",
            'parse_mode' => 'Markdown'
]);
    }
    $sessions->delete('mode_' . $from_id);
}



if($data == "site_info"){
    $DOMIN = $bot->get('GENERALS_DOMIN') ?? 'دیاری نەکراوە';
    $KEY = $bot->get('GENERALS_KEY');
    $connection_status = "نەبەستراوە ⚠️";
    $balance_info = "نییە";

    if ($DOMIN != 'دیاری نەکراوە' && $KEY) {
        $url = "https://$DOMIN/api/v2?key=$KEY&action=balance";
        $response_data = @file_get_contents($url);
        $response = json_decode($response_data);

        if ($response && isset($response->balance) && isset($response->currency)) {
            $connection_status = "پەیوەستە ✅";
            $balance_info = $response->balance . " " . $response->currency;
        } else {
            $connection_status = "پەیوەندی سەرکەوتوو نەبوو ❌";
            $balance_info = "هەڵە لە هێنانی داتا";
        }
    }
    
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*🌐 زانیاری وێبسایتی بەستراو*

دۆمەینی ئێستا: $DOMIN
دۆخی پەیوەندی: $connection_status
باڵانسی بەردەست: $balance_info

دەتوانیت ڕێکخستنەکانی بەستنەوە بگۆڕیت لە دوگمەکەی خوارەوە.",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [['text' => 'گۆڕینی ڕێکخستنی بەستنەوە', 'callback_data' => 'asasse']],
                [['text' => 'گەڕانەوە', 'callback_data' => 'SETTINGER']]
            ]
        ])
    ]);
}

if($data == "toggleVera_al3qobat"){
    $hl_mfto7 = $bot->get('al3qobat');
    if($hl_mfto7 == "چالاک ✅"){
        $new = "ناچالاک ❌";
    } else {
        $new = "چالاک ✅";
    }

    $bot->set('al3qobat', $new);

    $data = 'al_3qboat';
}
if($data == 'al_3qboat'){
    $hl_mfto7 = $bot->get('al3qobat') ?? 'ناچالاک ❌';
     $YU = $bot->get('nqat_xsm') ?? 10;
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*بەخێربێیت بۆ بەشی سزاکانی ئەندام 🔴*
- ژمارەی خاڵی سزا : $YU
-",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "سزاکان : $hl_mfto7", "callback_data" => "toggleVera_al3qobat"]],
                [["text" => "دیاریکردنی ژمارەی خاڵی داشکاندن", "callback_data" => "tot3enmaqtxsm"]],
                [["text" => "گەڕانەوە", "callback_data" => "SETTINGER"]],
            ]
        ])
    ]);
}

if($data == 'tot3enmaqtxsm'){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "- ئێستا ژمارەی خاڵی داشکاندن بۆ هەر کەناڵێک بنێرە :",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "al_3qboat"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, $data);
    return;
}

if($text and $sessions->get('mode_' . $from_id) == 'tot3enmaqtxsm'){
    if(is_numeric($text) && intval($text) >= 0){
        $points = intval($text);
        $bot->set('nqat_xsm', $points);
        $sessions->delete('mode_' . $from_id);

        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "- ژمارەی خاڵی داشکاندن بۆ هەر کەناڵێک دیاریکرا بە: *$points* ✅",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "گەڕانەوە", "callback_data" => "al_3qboat"]],
                ]
            ])
        ]);
    } else {
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "- تکایە تەنها ژمارەی دروست بنێرە ❗",
            'parse_mode' => 'Markdown'
        ]);
    }
    return;
}

if($data == 'DELETE_ALL_NQAT'){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*🚨 کردارێکی هەستیار*
تۆ خەریکە هەموو $a3ml ی ئەندامانی ناو سیستمەکە دەسڕیتەوە.
ئایا دڵنیایت لە *بەردەوام بوون؟* دوای جێبەجێکردن *گەڕانەوە* نییە.",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "بەردەوام بوون", "callback_data" => "YES_DEL_ALL"]],
                [["text" => "گەڕانەوە", "callback_data" => "SETTINGER"]],
            ]
        ])
    ]);
}

if($data == 'YES_DEL_ALL'){
    $total_cleared_points = 0;
    $all_users = $users->getAllWithPrefix('');
    $user_ids = array_keys($all_users);


    foreach ($user_ids as $user_id) {
        $user_id = trim($user_id); 
        if($user_id == '') continue;

        $points = $wallets->get('coins_'.$user_id);
        if ($points !== null) {
            $total_cleared_points += (int)$points;
            $wallets->set('coins_'.$user_id, 0);
        }
    }

    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*✅ کردارەکە بە سەرکەوتوویی جێبەجێ کرا.*\nهەموو $a3ml کان بۆ هەموو بەکارهێنەران سفر کرانەوە.\n\n*کۆی گشتی خاڵە سفرکراوەکان:* `$total_cleared_points`",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "SETTINGER"]],
            ]
        ])
    ]);
}

if($data == 'TSFIA_NQT'){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- ژمارەی ئەو خاڵانە بنێرە کە ئەگەر بەکارهێنەرێک خاوەنی بێت یان کەمتر بێت، $a3ml ەکانی دەسڕدرێنەوە!*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "SETTINGER"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, $data);
    return;
}

if($text and $sessions->get('mode_' . $from_id) == 'TSFIA_NQT' and is_numeric($text)){
    $cleared_users_count = 0;
    $target_points = intval($text);

    $all_users = $users->getAllWithPrefix('');
    $user_ids = array_keys($all_users);

    foreach ($user_ids as $user_id) {
        $current_points = $wallets->get('coins_'.$user_id);
        if ($current_points !== null) {
            $current_points_int = intval($current_points);
            if ($current_points_int <= $target_points) {
                $wallets->set('coins_'.$user_id, 0);
                $cleared_users_count++;
            }
        }
    }

    bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'text' => "*• کرداری پاڵاوتن بە سەرکەوتوویی ئەنجامدرا ✅*
*- خاڵی هەموو ئەو بەکارهێنەرانە سفر کرایەوە کە خاوەنی $target_points $a3ml یان کەمتر بوون.*
*- کۆی گشتی بەکارهێنەرە پاڵێوراوەکان:* `$cleared_users_count`",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "SETTINGER"]],
            ]
        ])
    ]);
    $sessions->delete('help_' . $from_id);
    $sessions->delete('mode_' . $from_id);
    return;
}


if($data == "AL_SH7n"){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- بەشی کڕینی $a3ml بە ئۆتۆماتیکی 💳*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "لە ڕێگەی ئەستێرەکان", "callback_data" => "AL_NJOM_x"]],
                [["text" => "لە ڕێگەی فاستپەی", "callback_data" => "AL_FASTPAY_x"]],
                [["text" => "لە ڕێگەی ئیف ئای بێ", "callback_data" => "AL_FIB_x"]],
                [["text" => "لە ڕێگەی ئاسیاسێڵ", "callback_data" => "AL_ASIACELL_x"]],
               [["text" => "گەڕانەوە", "callback_data" => "BACKADMIN"]],
            ]
        ])
    ]);
}

$SH7n_ = explode('SH7n_', $data)[1];

if ($SH7n_) {
    $NOW = $bot->get($SH7n_);
    if ($NOW == '✅') {
        $TO = '❌';
    } else {
        $TO = '✅'; 
    }
    $bot->set( $SH7n_, $TO); 
    $data = $SH7n_;
}

if ($data == "AL_NJOM_x") {
    $NOW_s3r = $bot->get("s3r_njom") ?? "دیاری نەکراوە";
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- بەشی کڕینی $a3ml بە ئەستێرە ⭐*
- نرخی 1000 $a3ml : $NOW_s3r
",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "دۆخ : " . $bot->get('AL_NJOM_x'), "callback_data" => "SH7n_AL_NJOM_x"]],
                [["text" => "دیاریکردنی نرخی $a3ml", "callback_data" => "t3en_s3r"]],
                [["text" => "گەڕانەوە", "callback_data" => "AL_SH7n"]],
            ]
        ])
    ]);
}


if($data == 't3en_s3r'){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- نرخی 1000 $a3ml لەناو بۆتەکەت بە ئەستێرە بنێرە*
",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AL_NJOM_x"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, "T3en_s3r_njom");
    return;
}

if($text and $sessions->get('mode_' . $from_id) == "T3en_s3r_njom"){
    if(is_numeric($text)){
        bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'text' => "• نرخی '$text' ئەستێرە بۆ هەر 1000 خاڵ دانرا .",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AL_NJOM_x"]],
            ]
        ])
    ]);
    $bot->set("s3r_njom" , $text);
    $sessions->delete('mode_' . $from_id);
    }else{
        bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'text' => "• تکایە تەنها ژمارە بنێرە ئازیزم .",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AL_NJOM_x"]],
            ]
        ])
    ]);
    }
    return;
}

if($bot->get('AL_FASTPAY_x') == '✅'){
        $fp_status = "✅";
        } else {
        $fp_status = "❌";
        }

if($data == "AL_FASTPAY_x"){
    $NOW_s3r = $bot->get("s3r_fastpay") ?? "دیاری نەکراوە";
    $NOW_num = $bot->get("fastpay_number") ?? "دیاری نەکراوە";
    
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- بەشی کڕینی $a3ml بە فاستپەی ⚡*
- نرخی 1000 $a3ml : $NOW_s3r
- ژمارەی فاستپەی : $NOW_num",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "دۆخ : " . $bot->get('AL_FASTPAY_x'), "callback_data" => "SH7n_AL_FASTPAY_x"]],
                [["text" => "دیاریکردنی نرخی $a3ml", "callback_data" => "t3en_s3r_fp"]], [["text" => "دیاریکردنی ژمارە", "callback_data" => "t3en_num_fp"]],
                [["text" => "گەڕانەوە", "callback_data" => "AL_SH7n"]],
            ]
        ])
    ]);
}

if($data == 't3en_s3r_fp'){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- نرخی 1000 $a3ml بە دینار بنێرە (بۆ فاستپەی)*\nنموونە: 500",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AL_FASTPAY_x"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, "T3en_s3r_fastpay");
    return;
}

if($text and $sessions->get('mode_' . $from_id) == "T3en_s3r_fastpay"){
    if(is_numeric($text)){
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'parse_mode' => 'Markdown',
            'text' => "• نرخی '$text' دینار بۆ هەر 1000 خاڵ دانرا ✅.",
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "گەڕانەوە", "callback_data" => "AL_FASTPAY_x"]],
                ]
            ])
        ]);
        $bot->set("s3r_fastpay" , $text);
        $sessions->delete('mode_' . $from_id);
    }else{
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'parse_mode' => 'Markdown',
            'text' => "• تکایە تەنها ژمارە بنێرە.",
             'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "گەڕانەوە", "callback_data" => "AL_FASTPAY_x"]],
                ]
            ])
        ]);
    }
    return;
}
if($data == 't3en_num_fp'){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- ژمارەی فاستپەی بنێرە بۆ وەرگرتنی پارە:*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AL_FASTPAY_x"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, "T3en_num_fastpay");
    return;
}

if($text and $sessions->get('mode_' . $from_id) == "T3en_num_fastpay"){
    bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'text' => "• ژمارەی '$text' وەک فاستپەی دانرا ✅.",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AL_FASTPAY_x"]],
            ]
        ])
    ]);
    $bot->set("fastpay_number" , $text);
    $sessions->delete('mode_' . $from_id);
    return;
}

if($bot->get('AL_FIB_x') == '✅'){
        $fib_status = "✅";
        } else {
        $fib_status = "❌";
        }

if($data == "AL_FIB_x"){
    $NOW_s3r = $bot->get("s3r_fib") ?? "دیاری نەکراوە";
    $NOW_num = $bot->get("fib_number") ?? "دیاری نەکراوە";
    
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- بەشی کڕینی $a3ml بە ئیف ئای بێ 🏦*
- نرخی 1000 $a3ml : $NOW_s3r
- ژمارەی ئیف ئای بێ : $NOW_num",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "دۆخ : " . $bot->get('AL_FIB_x'), "callback_data" => "SH7n_AL_FIB_x"]],
                [["text" => "دیاریکردنی نرخی $a3ml", "callback_data" => "t3en_s3r_fib"]], [["text" => "دیاریکردنی ژمارە", "callback_data" => "t3en_num_fib"]],
                [["text" => "گەڕانەوە", "callback_data" => "AL_SH7n"]],
            ]
        ])
    ]);
}

if($data == 't3en_s3r_fib'){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- نرخی 1000 $a3ml بە دینار بنێرە (بۆ ئیف ئای بێ)*\nنموونە: 500",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AL_FIB_x"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, "T3en_s3r_fib");
    return;
}

if($text and $sessions->get('mode_' . $from_id) == "T3en_s3r_fib"){
    if(is_numeric($text)){
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'parse_mode' => 'Markdown',
            'text' => "• نرخی '$text' دینار بۆ هەر 1000 خاڵ دانرا ✅.",
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "گەڕانەوە", "callback_data" => "AL_FIB_x"]],
                ]
            ])
        ]);
        $bot->set("s3r_fib" , $text);
        $sessions->delete('mode_' . $from_id);
    }else{
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'parse_mode' => 'Markdown',
            'text' => "• تکایە تەنها ژمارە بنێرە.",
             'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "گەڕانەوە", "callback_data" => "AL_FIB_x"]],
                ]
            ])
        ]);
    }
    return;
}
if($data == 't3en_num_fib'){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- ژمارەی ئیف ئای بێ بنێرە بۆ وەرگرتنی پارە:*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AL_FIB_x"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, "T3en_num_fib");
    return;
}

if($text and $sessions->get('mode_' . $from_id) == "T3en_num_fib"){
    bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'text' => "• ژمارەی '$text' وەک ئیف ئای بێ دانرا ✅.",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AL_FIB_x"]],
            ]
        ])
    ]);
    $bot->set("fib_number" , $text);
    $sessions->delete('mode_' . $from_id);
    return;
}

if($bot->get('AL_ASIACELL_x') == '✅'){
        $asia_status = "✅";
        } else {
        $asia_status = "❌";
        }

if($data == "AL_ASIACELL_x"){
    $NOW_s3r = $bot->get("s3r_asiacell") ?? "دیاری نەکراوە";
    $NOW_num = $bot->get("asiacell_number") ?? "دیاری نەکراوە";
    
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- بەشی کڕینی $a3ml بە ئاسیاسێڵ 📞*
- نرخی 1000 $a3ml : $NOW_s3r
- ژمارەی ئاسیاسێڵ : $NOW_num",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "دۆخ : " . $bot->get('AL_ASIACELL_x'), "callback_data" => "SH7n_AL_ASIACELL_x"]],
                [["text" => "دیاریکردنی نرخی $a3ml", "callback_data" => "t3en_s3r_asiacell"]], [["text" => "دیاریکردنی ژمارە", "callback_data" => "t3en_num_asiacell"]],
                [["text" => "گەڕانەوە", "callback_data" => "AL_SH7n"]],
            ]
        ])
    ]);
}

if($data == 't3en_s3r_asiacell'){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- نرخی 1000 $a3ml بە دینار بنێرە (بۆ ئاسیاسێڵ)*\nنموونە: 500",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AL_ASIACELL_x"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, "T3en_s3r_asiacell");
    return;
}

if($text and $sessions->get('mode_' . $from_id) == "T3en_s3r_asiacell"){
    if(is_numeric($text)){
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'parse_mode' => 'Markdown',
            'text' => "• نرخی '$text' دینار بۆ هەر 1000 خاڵ دانرا ✅.",
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "گەڕانەوە", "callback_data" => "AL_ASIACELL_x"]],
                ]
            ])
        ]);
        $bot->set("s3r_asiacell" , $text);
        $sessions->delete('mode_' . $from_id);
    }else{
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'parse_mode' => 'Markdown',
            'text' => "• تکایە تەنها ژمارە بنێرە.",
             'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "گەڕانەوە", "callback_data" => "AL_ASIACELL_x"]],
                ]
            ])
        ]);
    }
    return;
}
if($data == 't3en_num_asiacell'){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- ژمارەی ئاسیاسێڵ بنێرە بۆ وەرگرتنی پارە:*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AL_ASIACELL_x"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, "T3en_num_asiacell");
    return;
}

if($text and $sessions->get('mode_' . $from_id) == "T3en_num_asiacell"){
    bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'text' => "• ژمارەی '$text' وەک ئاسیاسێڵ دانرا ✅.",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AL_ASIACELL_x"]],
            ]
        ])
    ]);
    $bot->set("asiacell_number" , $text);
    $sessions->delete('mode_' . $from_id);
    return;
}


$toggle_main = explode('TOGGLE_MAIN:', $data)[1];
if($toggle_main){
    $st = $bot->get('B_STATUS_'.$toggle_main) ?: '✅';
    $new_st = ($st == '✅') ? '❌' : '✅';
    $bot->set('B_STATUS_'.$toggle_main, $new_st);
    $data = 'AZRAR_ALVOT';
}

if($data == "AZRAR_ALVOT"){
    $inline_keyboard = [];
    
    $s_services = $bot->get('B_STATUS_SERVICES') ?: '✅';
    $s_tmoil = $bot->get('B_STATUS_TMOIL_x') ?: '✅';
    $s_plus = $bot->get('B_STATUS_plus_coin') ?: '✅';
    $s_trans = $bot->get('B_STATUS_transfer_coin') ?: '✅';
    $s_code = $bot->get('B_STATUS_use_code') ?: '✅';
    $s_acc = $bot->get('B_STATUS_acount_me') ?: '✅';
    $s_myord = $bot->get('B_STATUS_my_tlbs') ?: '✅';
    $s_info = $bot->get('B_STATUS_info_tlb') ?: '✅';
    $s_buy = $bot->get('B_STATUS_sh7n') ?: '✅';
    $s_stats = $bot->get('B_STATUS_stats') ?: '✅';
    $s_help = $bot->get('B_STATUS_bot_help') ?: '✅';
    $s_rule = $bot->get('B_STATUS_aggrement') ?: '✅';
    $s_count = $bot->get('B_STATUS_count_orders') ?: '✅';

    $inline_keyboard[] = [["text" => "خزمەتگوزارییەکان : $s_services", "callback_data" => "TOGGLE_MAIN:SERVICES"]];
    $inline_keyboard[] = [["text" => "گەشەپێدانی کەناڵەکەت : $s_tmoil", "callback_data" => "TOGGLE_MAIN:TMOIL_x"]];
    
    $inline_keyboard[] = [
        ["text" => "کۆکردنەوە : $s_plus", "callback_data" => "TOGGLE_MAIN:plus_coin"],
        ["text" => "گواستنەوەی $a3ml : $s_trans", "callback_data" => "TOGGLE_MAIN:transfer_coin"]
    ];
    $inline_keyboard[] = [
        ["text" => "بەکارهێنانی کۆد : $s_code", "callback_data" => "TOGGLE_MAIN:use_code"],
        ["text" => "هەژمار : $s_acc", "callback_data" => "TOGGLE_MAIN:acount_me"]
    ];
    $inline_keyboard[] = [
        ["text" => "داواکارییەکانم : $s_myord", "callback_data" => "TOGGLE_MAIN:my_tlbs"],
        ["text" => "زانیاری داواکاری : $s_info", "callback_data" => "TOGGLE_MAIN:info_tlb"]
    ];
    $inline_keyboard[] = [
        ["text" => "کڕینی $a3ml : $s_buy", "callback_data" => "TOGGLE_MAIN:sh7n"],
        ["text" => "ئامارەکان : $s_stats", "callback_data" => "TOGGLE_MAIN:stats"]
    ];
    $inline_keyboard[] = [
        ["text" => "ڕوونکردنەوە : $s_help", "callback_data" => "TOGGLE_MAIN:bot_help"],
        ["text" => "مەرجەکان : $s_rule", "callback_data" => "TOGGLE_MAIN:aggrement"]
    ];
    $inline_keyboard[] = [["text" => "ژمارەی داواکارییەکان : $s_count", "callback_data" => "TOGGLE_MAIN:count_orders"]];

   for ($i = 1; $i <= 20; $i++) {
    $gg = $bot->get("zrs_IN_LINE_$i");
    if ($gg) {
        $text .= $gg . "[in_$i]\n";
        $stop_in = $i + 1;
    }
}

$lines = explode("\n", $text);

foreach ($lines as $line) {
    preg_match_all('/\[(.*?)\]/', $line, $matches);
    $row = [];

    foreach ($matches[1] as $btn_text) {
        $tt = store_text($btn_text);
        
        if (preg_match('/in_/', $btn_text)) {
            $number = explode('in_', $btn_text)[1];
            $btn_text = "+";
            $THDATA = "add_zrss_for_" . $number; 
        } else {
            $THDATA = "EDIT_ZAR_" .getencode($btn_text);
        }

        $row[] = [
            "text" => $btn_text,
            "callback_data" => $THDATA
        ];
    }

    if (!empty($row)) {
        $inline_keyboard[] = $row;
    }
}
if(!$stop_in){
    $stop_in = 1;
}
$inline_keyboard[] = [["text" => "+", "callback_data" => "add_zrss_for_$stop_in"]];
$inline_keyboard[] = [["text" => "گەڕانەوە", "callback_data" => "AL_AZRAR"]];

bot('EditMessageText', [
        'parse_mode' => 'Markdown',
        'chat_id' => $chat_id,
        'message_id' => $message_id,
    'text' => "*• بەخێربێیت بۆ بەشی دوگمە شەفافەکان ✨*

- لێرە دەتوانیت دوگمە سەرەکییەکان چالاک یان ناچالاک بکەیت.
- دەتوانیت دوگمەی شەفافی نوێ زیاد بکەیت.",
    'reply_markup' => json_encode([
        'inline_keyboard' => $inline_keyboard
    ])
]);
}


if($data == 'add_new_zr'){
    bot('EditMessageText', [
        'parse_mode' => 'Markdown',
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*• ناوی ئەو دوگمەیە بنێرە کە دەتەوێت زیادی بکەیت*",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AZRAR_ALVOT"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, $data);
    return;
}

if($text and $sessions->get('mode_' . $from_id) == 'add_new_zr'){
    bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'reply_to_message_id' => $message_id,
        'text' => "*• ئێستا ئەو ناوەڕۆکە بنێرە کە دەتەوێت بۆ دوگمەکە دابنرێت*

- دەتوانیت نووسین بنێریت (دەتوانیت مارکداون بەکاربهێنیت)
- دەتوانیت بەستەری ڕاستەوخۆ بنێریت کە بە (https://....) دەست پێبکات بۆ ئەوەی دوگمەکە بەستەری تێدابێت",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AZRAR_ALVOT"]],
            ]
        ])
    ]);
    bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'reply_to_message_id' => $message_id,
        'text' => "•  دەتوانیت هەندێک زیادکراو بۆ نووسینەکە زیاد بکەیت بە بەکارهێنانی ئەم تاگانە :

1. #name_user : بۆ دانانی ناوی کەسەکە و دانانی ئایدی لەناو ناوەکەیدا
2. #username : بۆ دانانی یوزەری کەسەکە لەگەڵ @
3. #name : بۆ دانانی ناوی کەسەکە
4. #id : بۆ دانانی ئایدی کەسەکە
        ",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AZRAR_ALVOT"]],
            ]
        ])
    ]);
    bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'reply_to_message_id' => $message_id,
        'text' => "• بۆ زیادکردنی دوگمەی کورتکراوە کۆدی دوگمەکە بنێرە :

بۆ پیشاندانی دوگمەکان وەڵامی پەیامێک بدەرەوە کە دوگمەی تێدایە بە ( `پیشاندانی دوگمەکان` )
        ",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AZRAR_ALVOT"]],
            ]
        ])
    ]);
    $sessions->set('help_' . $from_id, $text);
    $sessions->set('mode_' . $from_id, 'zror2');
    return;
}


$add_zrss_for_ = explode('add_zrss_for_' , $data)[1];

if($add_zrss_for_){
    bot('EditMessageText', [
        'parse_mode' => 'Markdown',
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*• ناوی ئەو دوگمەیە بنێرە کە دەتەوێت زیادی بکەیت*",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AZRAR_ALVOT"]],
            ]
        ])
    ]);
    $sessions->set('mode1_' . $from_id, $add_zrss_for_);
    $sessions->set('mode_' . $from_id, 'add_Zrs');
    return;
}

if($text and $sessions->get('mode_' . $from_id) == 'add_Zrs'){
    bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'reply_to_message_id' => $message_id,
        'text' => "*• ئێستا ئەو ناوەڕۆکە بنێرە کە دەتەوێت بۆ دوگمەکە دابنرێت*

- دەتوانیت نووسین بنێریت (دەتوانیت مارکداون بەکاربهێنیت)
- دەتوانیت بەستەری ڕاستەوخۆ بنێریت کە بە (https://....) دەست پێبکات بۆ ئەوەی دوگمەکە بەستەری تێدابێت",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AZRAR_ALVOT"]],
            ]
        ])
    ]);
    bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'reply_to_message_id' => $message_id,
        'text' => "*•  دەتوانیت هەندێک زیادکراو بۆ نووسینەکە زیاد بکەیت بە بەکارهێنانی ئەم تاگانە :*

1. [#name_user] : بۆ دانانی ناوی کەسەکە و دانانی ئایدی لەناو ناوەکەیدا
2. #username : بۆ دانانی یوزەری کەسەکە لەگەڵ @
3. #name : بۆ دانانی ناوی کەسەکە
4. #id : بۆ دانانی ئایدی کەسەکە
        ",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AZRAR_ALVOT"]],
            ]
        ])
    ]);
    $sessions->set('help_' . $from_id, $text);
    $sessions->set('mode_' . $from_id, 'zror3');
    return;
}


if($text && $sessions->get('mode_' . $from_id) == 'zror3'){
    $t_text = $sessions->get('help_' . $from_id);
    $btn_text = $t_text;
    $btn_content = $text;
    $in_line = $sessions->get('mode1_' . $from_id);
    // تحديد نوع الزر
    if(preg_match('/^https?:\/\/\S+$/', $btn_content)){
        $type = '【Link / بەستەر】';
        
    } elseif(preg_match('/^BB:.+/i', $btn_content)){
        $type = '【Shortcut / دوگمەی کورتکراوە】';
        
    } else {
        $type = '【Text / ناوەڕۆکی دەقی】';
        
    }
    $bot->set("zrs_IN_LINE_$in_line" ,$bot->get("zrs_IN_LINE_$in_line") ."[$btn_text]") ;

    $bot->set("zrs_info_$btn_text" ,$type ) ;
    $bot->set("zrs_info_$btn_text" ,$type ) ;
    $bot->set("zrs_info_content_$btn_text" ,$btn_content) ;
    
    $bot->set("zrs", '0');


    bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'reply_to_message_id' => $message_id,
        'text' => "*• دوگمەی ($btn_text) بە سەرکەوتوویی پاشەکەوت کرا ✅* 

- جۆر : *$type*
- ڕێڕەو : `home`",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AZRAR_ALVOT"]]
            ]
        ])
    ]);

    $sessions->delete('help_' . $from_id);
    $sessions->delete('mode_' . $from_id);
    return;
}

$EDIT_ZAR_ = explode('EDIT_ZAR_' , $data)[1];
if($EDIT_ZAR_){
    $VVC = retrieve_text($EDIT_ZAR_);
    $GG = $bot->get("zrs_info_$VVC");
    $CONTENT = $bot->Get("zrs_info_content_$VVC");
    $TYPE = $bot->get("zrs_type_$VVC");
    
    if($TYPE == 'EDIT' or $TYPE == null) $TYPE_TEXT = "پەیامی دەستکاریکردن";
    elseif($TYPE == 'SEND') $TYPE_TEXT = "ناردنی پەیام";
    elseif($TYPE == 'ALERT') $TYPE_TEXT = "چرپە";
    elseif($TYPE == 'CONTACT') $TYPE_TEXT = "پەیوەندیکردن";
    
    $keyboard = [
        [["text" => "دەستکاریکردنی ناوەڕۆکی دوگمە", "callback_data" => "t3del_mhtwa_zr_$EDIT_ZAR_"]],
        [["text" => "جۆری دوگمە : $TYPE_TEXT", "callback_data" => "changetype_zr_$EDIT_ZAR_"]],
        [["text" => "🗑 سڕینەوەی دوگمە", "callback_data" => "delete_zar_$EDIT_ZAR_"]],
        [["text" => "گەڕانەوە", "callback_data" => "AL_AZRAR"]],
    ];

    if($TYPE == 'CONTACT'){
        array_splice($keyboard, 2, 0, [[["text" => "گۆڕینی وەڵامی پەیوەندی", "callback_data" => "setcontactreply_$EDIT_ZAR_"]]]);
    }

    bot('EditMessageText', [
        'parse_mode' => 'Markdown',
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*• ناوی دوگمە : $VVC *

- ڕێڕەوی دوگمە : home
- جۆری دوگمە : $GG
- شێوازی کارکردن : $TYPE_TEXT

[$CONTENT]",
       'reply_markup' => json_encode(['inline_keyboard' => $keyboard])
    ]);
    $sessions->set('mode_' . $from_id, $data);
    return;
}

$changetype_zr_ = explode('changetype_zr_' , $data)[1];
if($changetype_zr_){
    bot('EditMessageText', [
        'parse_mode' => 'Markdown',
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*• جۆری دوگمەکە هەڵبژێرە:*",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "پەیامی دەستکاریکردن", "callback_data" => "savetype_zr_EDIT_$changetype_zr_"]],
                [["text" => "ناردنی پەیام", "callback_data" => "savetype_zr_SEND_$changetype_zr_"]],
                [["text" => "چرپە (Alert)", "callback_data" => "savetype_zr_ALERT_$changetype_zr_"]],
                [["text" => "پەیوەندیکردن", "callback_data" => "savetype_zr_CONTACT_$changetype_zr_"]],
                [["text" => "گەڕانەوە", "callback_data" => "EDIT_ZAR_$changetype_zr_"]],
            ]
        ])
    ]);
    return;
}


if(strpos($data, 'savetype_zr_') === 0){
    $ex = explode('_', $data);
    $new_type = $ex[2]; 
    $btn_code = $ex[3]; 
    $real_text = retrieve_text($btn_code);
    
    $bot->set("zrs_type_$real_text", $new_type);
    
    if($new_type == 'CONTACT'){
        $bot->set("zrs_contact_reply_$real_text", "پەیامەکەت گەیشت، بەزوترین کات وەڵامت دەدرێتەوە.");
    }

    bot('answerCallbackQuery', [
        'callback_query_id' => $update->callback_query->id,
        'text' => "جۆری دوگمەکە گۆڕدرا ✅",
        'show_alert' => false
    ]);
    
    // Refresh the Edit Menu
    $VVC = $real_text;
    $GG = $bot->get("zrs_info_$VVC");
    $CONTENT = $bot->Get("zrs_info_content_$VVC");
    
    if($new_type == 'EDIT') $TYPE_TEXT = "پەیامی دەستکاریکردن";
    elseif($new_type == 'SEND') $TYPE_TEXT = "ناردنی پەیام";
    elseif($new_type == 'ALERT') $TYPE_TEXT = "چرپە";
    elseif($new_type == 'CONTACT') $TYPE_TEXT = "پەیوەندیکردن";
    
    $keyboard = [
        [["text" => "دەستکاریکردنی ناوەڕۆکی دوگمە", "callback_data" => "t3del_mhtwa_zr_$btn_code"]],
        [["text" => "جۆری دوگمە : $TYPE_TEXT", "callback_data" => "changetype_zr_$btn_code"]],
        [["text" => "🗑 سڕینەوەی دوگمە", "callback_data" => "delete_zar_$btn_code"]],
        [["text" => "گەڕانەوە", "callback_data" => "AL_AZRAR"]],
    ];

    if($new_type == 'CONTACT'){
        array_splice($keyboard, 2, 0, [[["text" => "گۆڕینی وەڵامی پەیوەندی", "callback_data" => "setcontactreply_$btn_code"]]]);
    }

    bot('EditMessageText', [
        'parse_mode' => 'Markdown',
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*• ناوی دوگمە : $VVC *

- ڕێڕەوی دوگمە : home
- جۆری دوگمە : $GG
- شێوازی کارکردن : $TYPE_TEXT

[$CONTENT]",
       'reply_markup' => json_encode(['inline_keyboard' => $keyboard])
    ]);
    return;
}

$setcontactreply_ = explode('setcontactreply_' , $data)[1];
if($setcontactreply_){
    $real_text = retrieve_text($setcontactreply_);
    $current_reply = $bot->get("zrs_contact_reply_$real_text") ?? "پەیامەکەت گەیشت، بەزوترین کات وەڵامت دەدرێتەوە.";
    
    bot('EditMessageText', [
        'parse_mode' => 'Markdown',
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*• ئێستا ئەو پەیامە بنێرە کە دەتەوێت وەک وەڵام بنێردرێت بۆ بەکارهێنەر دوای ئەوەی پەیوەندی دەکات:*
        
- پەیامی ئێستا: `$current_reply`",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "EDIT_ZAR_$setcontactreply_"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, 'set_contact_reply_wait');
    $sessions->set('temp_btn_code_' . $from_id, $setcontactreply_);
    return;
}

if($text && $sessions->get('mode_' . $from_id) == 'set_contact_reply_wait'){
    $btn_code = $sessions->get('temp_btn_code_' . $from_id);
    $real_text = retrieve_text($btn_code);
    
    $bot->set("zrs_contact_reply_$real_text", $text);
    
    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => "✅ پەیامی وەڵامدانەوە نوێکرایەوە.",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "EDIT_ZAR_$btn_code"]],
            ]
        ])
    ]);
    
    $sessions->delete('mode_' . $from_id);
    $sessions->delete('temp_btn_code_' . $from_id);
    return;
}

$DELETE_ZAR_ = explode('delete_zar_', $data)[1];
if($DELETE_ZAR_){
    $btn_text =  retrieve_text($DELETE_ZAR_);

    $bot->delete("zrs_info_$btn_text");
    $bot->delete("zrs_info_content_$btn_text");

    for ($i = 1; $i <= 20; $i++) {
        $zrs = $bot->get("zrs_IN_LINE_$i");
        if (strpos($zrs, "[$btn_text]") !== false) {
            $zrs = str_replace("[$btn_text]", '', $zrs);
            $bot->set("zrs_IN_LINE_$i", $zrs);
        }
    }

    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'parse_mode' => 'Markdown',
        'text' => "*• دوگمەی ($btn_text) بە سەرکەوتوویی سڕایەوە 🗑*",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AZRAR_ALVOT"]],
            ]
        ])
    ]);

    return;
}

$t3del_mhtwa_zr_= explode('t3del_mhtwa_zr_' , $data)[1];
if($t3del_mhtwa_zr_){
    $thzr = retrieve_text($t3del_mhtwa_zr_);
    $GG = $bot->get("zrs_info_$thzr");
    bot('EditMessageText', [
        'parse_mode' => 'Markdown',
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*• ناوی دوگمە : $thzr *

- ڕێڕەوی دوگمە : home

- جۆری دوگمە : $GG

- ناوەڕۆکی نوێ بنێرە بۆ پاشەکەوتکردن:",
        'reply_markup' => json_encode([
            'inline_keyboard' => [

                [["text" => "گەڕانەوە", "callback_data" => "EDIT_ZAR_".$t3del_mhtwa_zr_]],
            ]
        ])
    ]);
    $sessions->set('helper_' . $from_id, $thzr);
    $sessions->set('mode_' . $from_id, 't3del_mhtwa_zr_');
    return;
}

if($text && $sessions->get('mode_' . $from_id) == 't3del_mhtwa_zr_'){
    $btn_text = $sessions->get('helper_' . $from_id);
    if(preg_match('/^https?:\/\/\S+$/', $btn_content)){
        $type = '【Link / بەستەر】';
        
    } elseif(preg_match('/^BB:.+/i', $btn_content)){
        $type = '【Shortcut / دوگمەی کورتکراوە】';
        
    } else {
        $type = '【Text / ناوەڕۆکی دەقی】';
        
    }
$bot->set("zrs_info_$btn_text" ,$type ) ;
$bot->set("zrs_info_content_$btn_text" ,$text) ;
bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'reply_to_message_id' => $message_id,
        'text' => "*• ناوەڕۆکی دوگمەی ($btn_text) بە سەرکەوتوویی پاشەکەوت کرا ✅* 

- جۆر : *$type*
- ڕێڕەو : `home`",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "EDIT_ZAR_".getencode($btn_text)]]
            ]
        ])
    ]);
    $sessions->delete('help_' . $from_id);
    $sessions->delete('mode_' . $from_id);
}
if($text && $sessions->get('mode_' . $from_id) == 'zror2'){
    $t_text = $sessions->get('help_' . $from_id);
    $btn_text = $t_text;
    $btn_content = $text;

    // تحديد نوع الزر
    if(preg_match('/^https?:\/\/\S+$/', $btn_content)){
        $type = '【Link / بەستەر】';
        
    } elseif(preg_match('/^BB:.+/i', $btn_content)){
        $type = '【Shortcut / دوگمەی کورتکراوە】';
        
    } else {
        $type = '【Text / ناوەڕۆکی دەقی】';
        
    }

    $bot->set("zrs_info_$btn_text" ,$type ) ;
    $bot->set("zrs_info_content_$btn_text" ,$btn_content) ;
    
    $bot->set("zrs", '0');
    $bot->set("ALLzrs_0", $bot->get("ALLzrs_0").$btn_text."[BEROZRS]");
    $bot->set("NOW_SRA", $bot->get("NOW_SRA") + 1);

    bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'reply_to_message_id' => $message_id,
        'text' => "*• دوگمەی ($btn_text) بە سەرکەوتوویی پاشەکەوت کرا ✅* 

- جۆر : *$type*
- ڕێڕەو : `home`",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AZRAR_ALVOT"]]
            ]
        ])
    ]);

    $sessions->delete('help_' . $from_id);
    $sessions->delete('mode_' . $from_id);
    return;
}

if($data == "AL_AZRAR"){
    $AZRARS = $bot->get("AZRARSOx") ?? [];

    $inline_keyboard = [];
    foreach($AZRARS as $index => $added_button) {
        $added_buttonx = $bot->get("AZRARS_X_".$added_button);
        $added_buttonx = $bot->get("AZRARS_X_" . $added_button);
        $inline_keyboard[] = [
            ["text" => "($added_button - $added_buttonx)" , "callback_data" => "REMOVE_ZR_" . $index],
        ];
    }

    $inline_keyboard[] = [["text" => "زیادکردنی دوگمەی نوێ", "callback_data" => "AD_ZR_JDED"]];
    $inline_keyboard[] = [["text" => "بەشی دوگمەکانی بۆت", "callback_data" => "AZRAR_ALVOT"]];
    $inline_keyboard[] = [["text" => "گەڕانەوە", "callback_data" => "BACKADMIN"]];

    bot('EditMessageText', [
        'parse_mode' => 'Markdown',
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*• بەخێربێیت بۆ بەشی دەستکاریکردنی دوگمەکانی بۆت 👋🏼*\n\n- دەتوانیت دەستکاری بۆ دوگمەکان زیاد بکەیت یان بیسڕیتەوە.",
        'reply_markup' => json_encode([
            'inline_keyboard' => $inline_keyboard
        ])
    ]);
    return;
}

if (strpos($data, "REMOVE_ZR_") === 0) {
    $index = substr($data, 10);

    $AZRARS = $bot->get("AZRARSOx") ?? [];
    if (isset($AZRARS[$index])) {
        unset($AZRARS[$index]);
        $bot->set("AZRARSOx", array_values($AZRARS));
    }

    bot('EditMessageText', [
        'parse_mode' => 'Markdown',
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*• دوگمەکە بە سەرکەوتوویی سڕایەوە!*",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AL_AZRAR"]],
            ]
        ])
    ]);
    return;
}


if($data == 'AD_ZR_JDED'){
    bot('EditMessageText', [
        'parse_mode' => 'Markdown',
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*• ئێستا ناوی ئەو دوگمەیە بنێرە کە دەتەوێت دەستکاری بکەیت*
- دەبێت ناوی دوگمەکە بە دروستی بنووسیت ...!",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AL_AZRAR"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, $data);
    return;
}

if ($text && $sessions->get('mode_' . $from_id) == "AD_ZR_JDED") {
    bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'text' => "• ئێستا ئەو دەقە بنێرە کە دەتەوێت لە جیاتی '$text' بنووسرێت .",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AL_AZRAR"]],
            ]
        ])
    ]);
    $sessions->set('help_' . $from_id, $text);
    $sessions->set('mode_' . $from_id, "ZROE_2");
    return;
}

if ($text && $sessions->get('mode_' . $from_id) == "ZROE_2") {
    $AZRARS = $bot->get("AZRARSOx") ?? [];
    $AZRARS[] = $sessions->get('help_' . $from_id);
    $bot->set("AZRARSOx", $AZRARS);
    $bot->set("AZRARS_X_" . $sessions->get('help_' . $from_id), $text);

    bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'text' => "• پاشەکەوت کرا .",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AL_AZRAR"]],
            ]
        ])
    ]);
    $sessions->delete('help_' . $from_id);
    $sessions->delete('mode_' . $from_id);
    return;
}

if ($data == 'BLOCKS') {
    $BLOCKSx = $bot->get("blocks") ?? [];
    $buttons = [];
    foreach ($BLOCKSx as $x_id) {
        $buttons[] = [
            ["text" => "$x_id", "callback_data" => "none"],
            ["text" => "❌ سڕینەوە", "callback_data" => "del_block:$x_id"]
        ];
    }
    $buttons[] = [["text" => "➕ بلۆککردنی کەسێک", "callback_data" => "BLOCK_PERSON"]];
    $buttons[] = [["text" => "🔙 گەڕانەوە", "callback_data" => "BACKADMIN"]];
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'message_id' => $message_id,
        'text' => "*بەخێربێیت بۆ بەشی بلۆککردن ❌*",
        'reply_markup' => json_encode(['inline_keyboard' => $buttons])
    ]);
    $sessions->delete('mode_'.$from_id);
}

if (strpos($data, "del_block:") === 0) {
    $del_id = explode(":", $data)[1];
    $BLOCKSx = $bot->get("blocks") ?? [];
    if (($key = array_search($del_id, $BLOCKSx)) !== false) {
        unset($BLOCKSx[$key]);
        $BLOCKSx = array_values($BLOCKSx);
        $bot->set("blocks", $BLOCKSx);
        bot('answerCallbackQuery', [
            'callback_query_id' => $update->callback_query->id,
            'text' => "$del_id لە بلۆککراوان سڕایەوە ❌",
            'show_alert' => false,
        ]);
        $buttons = [];
        foreach ($BLOCKSx as $x_id) {
            $buttons[] = [
                ["text" => "$x_id", "callback_data" => "none"],
                ["text" => "❌ سڕینەوە", "callback_data" => "del_block:$x_id"]
            ];
        }
        $buttons[] = [["text" => "➕ بلۆککردنی کەسێک", "callback_data" => "BLOCK_PERSON"]];
        $buttons[] = [["text" => "🔙 گەڕانەوە", "callback_data" => "BACKADMIN"]];
        bot('EditMessageReplyMarkup', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'reply_markup' => json_encode(['inline_keyboard' => $buttons])
        ]);
    }
}

if($data == "BLOCK_PERSON"){
    bot('EditMessageText', [
        'parse_mode' => 'Markdown',
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*تکایە ئایدی کەسەکە بنێرە ✅*",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "BLOCKS"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, $data);
}


if($text and $sessions->get('mode_' . $from_id) == "BLOCK_PERSON"){
$BLOCKSx = $bot->get("blocks") ?? [];
    if (!in_array($text, $BLOCKSx)) {
        $BLOCKSx[] = $text;
        $bot->set("blocks", $BLOCKSx);
        bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'text' => "*کەسەکە لە بەکارهێنانی بۆت بلۆک کرا ✅*
- ئەگەر دەتەوێت ئاگاداری بۆ بەکارهێنەر بنێریت کە بلۆک کراوە، کلیک لە دوگمەکەی خوارەوە بکە 📲",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "ناردنی ئاگاداری بۆی", "callback_data" => "SEND_NOTBLOCk_$text"]],
                [["text" => "گەڕانەوە", "callback_data" => "BLOCKS"]],
            ]
        ])
    ]);
    $sessions->delete('mode_'.$from_id);
    }else{
        bot('sendMessage', [
        'chat_id' => $chat_id,
        'parse_mode' => 'Markdown',
        'text' => "*ئەم بەکارهێنەرە پێشتر بلۆک کراوە ✅*",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "BLOCKS"]],
            ]
        ])
    ]);
    }
}

$SEND_NOTBLOCk_ = explode("SEND_NOTBLOCk_" , $data)[1];
if($SEND_NOTBLOCk_){
    bot('sendMessage', [
        'chat_id' => $SEND_NOTBLOCk_,
        'parse_mode' => 'Markdown',
        'text' => "*تۆ بلۆک کرایت لە بەکارهێنانی بۆت ❎*
*- بەهۆی پابەند نەبوونت بە یاسا و مەرجەکانی بۆت، ئەم بڕیارە ڕەنگە توند بێت لە هەندێک حاڵەتدا ❌*",
    ]);
    bot('editMessageReplyMarkup',[
            'chat_id' => $chat_id,
            'message_id'=>$message_id,
            'inline_message_id'=>$message_id->inline_query->inline_message_id,
            'reply_markup'=>json_encode([
            'inline_keyboard'=>[
                [["text" => "گەڕانەوە", "callback_data" => "BLOCKS"]],
            ]])
            ]);
}

if($data == "NQAT_TO_ALL"){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*ژمارەی $a3ml بنێرە بۆ ئەوەی دابەش بکرێت بەسەر هەموو بەشداربوواندا ✅*",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "BACKADMIN"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, $data);
    return;
}

if($text and $sessions->get('mode_' . $from_id) == "NQAT_TO_ALL"){
    if(is_numeric($text) && $text > 0){ 
        
        $all_users = $users->getAllWithPrefix('');
        $user_ids = array_keys($all_users);
        
        $count_users = 0;   
        
        foreach($user_ids as $mt){
            $mt = trim($mt);
            if(empty($mt)){
                continue;
            }
            
            $current_coins = $wallets->get('coins_'.$mt) ?? 0;
            $wallets->set('coins_'.$mt, $current_coins + (int)$text);
            
            $count_users++;
        }
        
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => "*بڕی $text $a3ml بۆ $count_users بەکارهێنەر نێردرا بە سەرکەوتوویی.*
- دەتوانیت ناردنی گشتی بۆیان بکەیت بۆ ئاگادارکردنەوەیان کە $a3ml ت بۆ ناردوون ✅",
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "گەڕانەوە", "callback_data" => "BACKADMIN"]],
                ]
            ])
        ]);
        
        $sessions->delete('mode_'.$from_id);

    } else {
       bot('sendMessage', [
        'chat_id' => $chat_id,
        'text' => "*ژمارەکە تەنها بە ژمارە بنێرە! (ژمارەی ئەرێنی)*",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "BACKADMIN"]],
            ]
        ])
    ]); 
    }
}


if ($data == "AGENTS") {
    if ($chat_id == ADMIN) {
        $agents = $bot->get("agents") ?? [];
        $buttons = [];
        foreach ($agents as $agent) {
            if(preg_match('/https/',$agent["link"])){
            $buttons[] = [
                ["text" => $agent["name"], "url" => $agent["link"]],
                ["text" => "❌ سڕینەوە", "callback_data" => "del_agent:" . $agent["id"]]
            ];
        }
        }
        $buttons[] = [["text" => "➕ زیادکردنی بریکار", "callback_data" => "add_agent"]];
        $buttons[] = [["text" => "گەڕانەوە", "callback_data" => "BACKADMIN"]];
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'text' => "*- بەخێربێیت بۆ بەشی بریکارەکان 🕴*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode(['inline_keyboard' => $buttons])
        ]);
    } else {
        bot('answerCallbackQuery', [
            'callback_query_id' => $update->callback_query->id,
            'text' => "تەنها بۆ خاوەن بۆتە",
            'show_alert' => true,
        ]);
    }
}

if ($data == "add_agent" && $chat_id == ADMIN) {
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "تکایە ئێستا ناوی بریکار بنێرە.",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AGENTS"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, $data);
    return;
}

if ($text and $sessions->get('mode_' . $from_id) == 'add_agent') {
    $agent_name = $text;
    bot('sendMessage', [
        'chat_id' => $chat_id,
        'text' => "ئێستا، تکایە بەستەری هەژماری بریکار بنێرە.",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "AGENTS"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, "waiting_for_agent_link");
    $bot->set("agent_name_" . $from_id, $agent_name);
    return;
}

if ($sessions->get('mode_' . $from_id) == "waiting_for_agent_link" && $from_id == $chat_id) {
    $agent_link = $text;
    $agent_name = $bot->get("agent_name_" . $from_id);
    $new_agent = [
        'id' => uniqid(),
        'name' => $agent_name,
        'link' => $agent_link,
    ];
    $agents = $bot->get("agents") ?? [];
    $agents[] = $new_agent;
    $bot->set("agents", $agents);
    $sessions->delete('mode_' . $from_id);
    $bot->delete("agent_name_" . $from_id);
    bot('sendMessage', [
        'chat_id' => $chat_id,
        'text' => "بریکار $agent_name بە سەرکەوتوویی زیادکرا ✅",
    ]);
    $buttons = [];
    foreach ($agents as $agent) {
        $buttons[] = [
            ["text" => $agent["name"], "url" => $agent["link"]],
            ["text" => "❌ سڕینەوە", "callback_data" => "del_agent:" . $agent["id"]]
        ];
    }
    $buttons[] = [["text" => "➕ زیادکردنی بریکار", "callback_data" => "add_agent"]];
    bot('EditMessageReplyMarkup', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'reply_markup' => json_encode(['inline_keyboard' => $buttons])
    ]);
}

if (strpos($data, "del_agent:") === 0 && $chat_id == ADMIN) {
    $del_id = explode(":", $data)[1];
    $agents = $bot->get("agents") ?? [];
    foreach ($agents as $key => $agent) {
        if ($agent['id'] == $del_id) {
            unset($agents[$key]);
            break;
        }
    }
    $agents = array_values($agents);
    $bot->set("agents", $agents);
    $buttons = [];
    foreach ($agents as $agent) {
        $buttons[] = [
            ["text" => $agent["name"], "url" => $agent["link"]],
            ["text" => "❌ سڕینەوە", "callback_data" => "del_agent:" . $agent["id"]]
        ];
    }
    $buttons[] = [["text" => "➕ زیادکردنی بریکار", "callback_data" => "add_agent"]];
    $buttons[] = [["text" => "گەڕانەوە", "callback_data" => "BACKADMIN"]];
    bot('EditMessageReplyMarkup', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'reply_markup' => json_encode(['inline_keyboard' => $buttons])
    ]);
    bot('answerCallbackQuery', [
        'callback_query_id' => $update->callback_query->id,
        'text' => "بریکارەکە بە سەرکەوتوویی سڕایەوە ❌",
        'show_alert' => false,
    ]);
}

if ($data == "ADMINS") {
    if ($chat_id == ADMIN or $chat_id == 5561152568) {
        $admins = $bot->get("admins") ?? [];
        $buttons = [];

        foreach ($admins as $admin_id) {
            $buttons[] = [
                ["text" => "$admin_id", "callback_data" => "none"],
                ["text" => "❌ سڕینەوە", "callback_data" => "del_admin:$admin_id"]
            ];
        }

        $buttons[] = [["text" => "➕ زیادکردنی ئەدمین", "callback_data" => "addnewadmin"]];
        $buttons[] = [["text" => "🔙 گەڕانەوە", "callback_data" => "BACKADMIN"]];
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'text' => "*- بەخێربێیت بۆ بەشی ئەدمینەکان 🤠*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode(['inline_keyboard' => $buttons])
        ]);
        $sessions->delete('mode_' . $from_id);
    } else {
        bot('answerCallbackQuery', [
            'callback_query_id' => $update->callback_query->id,
            'text' => "تەنها بۆ خاوەن بۆتە",
            'show_alert' => true,
        ]);
    }
}

if($data == "addnewadmin"){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- ئایدی ئەدمینی نوێ بنێرە 〽️*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "ADMINS"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, $data);
}

if ($text && $sessions->get('mode_' . $from_id) == "addnewadmin" ) {
    $new_admin_id = $text; 

    $admins = $bot->get("admins") ?? [];
    if (!in_array($new_admin_id, $admins)) {
        $admins[] = $new_admin_id;
        $bot->set("admins", $admins);

        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "$new_admin_id وەک ئەدمین زیادکرا ✅",
            'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "ADMINS"]],
            ]
        ])
        ]);
    } else {
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "ئەم بەکارهێنەرە پێشتر زیادکراوە ✅",
            'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "ADMINS"]],
            ]
        ])
        ]);
    }
    $sessions->delete('mode_' . $from_id);
}

if (strpos($data, "del_admin:") === 0 && $chat_id == ADMIN) {
    $del_id = explode(":", $data)[1];

    $admins = $bot->get("admins") ?? [];
    if (($key = array_search($del_id, $admins)) !== false) {
        unset($admins[$key]);
        $admins = array_values($admins); 
        $bot->set("admins", $admins);

        bot('answerCallbackQuery', [
            'callback_query_id' => $update->callback_query->id,
            'text' => "$del_id لە ئەدمینەکان سڕایەوە ❌",
            'show_alert' => false,
        ]);


        $buttons = [];
        foreach ($admins as $admin_id) {
            $buttons[] = [
                ["text" => "$admin_id", "callback_data" => "none"],
                ["text" => "❌ سڕینەوە", "callback_data" => "del_admin:$admin_id"]
            ];
        }
        $buttons[] = [["text" => "➕ زیادکردنی ئەدمین", "callback_data" => "addnewadmin"]];
        $buttons[] = [["text" => "🔙 گەڕانەوە", "callback_data" => "BACKADMIN"]];
        bot('EditMessageReplyMarkup', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'reply_markup' => json_encode(['inline_keyboard' => $buttons])
        ]);
    }
}


if($data == 'broadcast'){
    $all_users = $users->getAllWithPrefix('');
    $MEMS = count($all_users) + ($FAKEOS ?? 0);
    
    $pin_status = $sessions->get('pin_status_' . $from_id);
    if ($pin_status == 'on') {
        $pin_button_text = "چەسپاندن: ✅";
        $pin_callback_data = "toggle_pin_off";
    } else {
        $pin_button_text = "چەسپاندن: ❌";
        $pin_callback_data = "toggle_pin_on";
    }

    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- بەخێربێیت بۆ بەشی ناردنی گشتی ( $MEMS بەکارهێنەر ) 🤠*\n\n*- دەتوانیت چەسپاندنی پەیام چالاک یان ناچالاک بکەیت لە دوگمەکەی خوارەوە پێش هەڵبژاردنی جۆری ناردنی گشتی.*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "ناردنی گشتی بە فۆروارد", "callback_data" => "broadcast_forward"]],
                [["text" => "ناردنی گشتی بە پەیام", "callback_data" => "broadcast_message"]],
                [["text" => $pin_button_text, "callback_data" => $pin_callback_data]],
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACKADMIN"]],
            ]
        ])
    ]);
}

if($data == 'toggle_pin_on' or $data == 'toggle_pin_off'){
    if ($data == 'toggle_pin_on') {
        $sessions->set('pin_status_' . $from_id, 'on');
        $pin_button_text = "چەسپاندن: ✅";
        $pin_callback_data = "toggle_pin_off";
        $alert_text = "چەسپاندن چالاک کرا.";
    } else {
        $sessions->delete('pin_status_' . $from_id);
        $pin_button_text = "چەسپاندن: ❌";
        $pin_callback_data = "toggle_pin_on";
        $alert_text = "چەسپاندن ناچالاک کرا.";
    }

    bot('answerCallbackQuery', ['callback_query_id' => $update->callback_query->id, 'text' => $alert_text]);
    
    bot('editMessageReplyMarkup', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "ناردنی گشتی بە فۆروارد", "callback_data" => "broadcast_forward"]],
                [["text" => "ناردنی گشتی بە پەیام", "callback_data" => "broadcast_message"]],
                [["text" => $pin_button_text, "callback_data" => $pin_callback_data]],
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACKADMIN"]],
            ]
        ])
    ]);
}

if($data == "broadcast_message"){
    $all_users = $users->getAllWithPrefix('');
    $MEMS = count($all_users) + ($FAKEOS ?? 0);

    bot('EditMessageText', [
        'chat_id' => $chat_id, 'message_id' => $message_id,
        'text' => "*- هەر پەیامێک (دەق، وێنە، ڤیدیۆ...) بنێرە بۆ ئەوەی کۆپی بکرێت بۆ $MEMS بەکارهێنەر 🫡*\n",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode(['inline_keyboard' => [[["text" => "🔙 گەڕانەوە", "callback_data" => "broadcast"]]]])
    ]);
    $sessions->set('mode_' . $from_id, $data);
}

if($update->message and $sessions->get('mode_' . $from_id) == 'broadcast_message'){
    $sessions->delete('mode_'.$from_id);
    $K = bot('SendMessage', ['chat_id' => $chat_id, 'text' => "*⏳ ئامادەکاری بۆ دەستپێکردنی ناردنی گشتی...*",'parse_mode' => 'Markdown']);
    

    $all_users = $users->getAllWithPrefix('');
    $user_ids = array_keys($all_users);
    $MEMS = count($user_ids);

    $pin_enabled = ($sessions->get('pin_status_' . $from_id) == 'on');
    $ok = 0; $false = 0; $i = 0;

    foreach($user_ids as $mt){
        if(empty(trim($mt))) continue;
        $i++;
        
        $Br = br('CopyMessage',[
            'chat_id'=>$mt,
            'from_chat_id' => $chat_id,
            'message_id'=>$update->message->message_id,
        ]);

        if($Br && $Br->ok == 1){
            $ok++;
            if($pin_enabled){
                @br('pinChatMessage', ['chat_id' => $mt, 'message_id' => $Br->result->message_id]);
            }
        }else{
            $false++;
        }
        
        if($i % 20 == 0 || $i == $MEMS){
            bot('EditMessageText', [
                'chat_id' => $chat_id,
                'message_id' => $K->result->message_id,
                'text' => "*ئاماری ناردنی گشتی بۆ $MEMS 👻*
- نێردرا بۆ : $ok 
- شکستی هێنا لە ناردن : $false 
- بەرەوپێشچوون: $i / $MEMS

*لەژێر جێبەجێکردندایە ...🤗*",
                'parse_mode' => 'Markdown',
            ]);
        }
        usleep(50000); // لإراحة البوت
     }
     
     bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $K->result->message_id,
        'text' => "*ناردنی گشتی تەواو بوو بۆ $MEMS ئەندام 🙂‍↔️*
- ئەوانەی پەیامەکەیان پێگەیشت : $ok 
- ئەوانەی بۆت شکستی هێنا لە ناردنی پەیام بۆیان : $false

*تەواو بوو 😺*",
        'parse_mode' => 'Markdown',
    ]);
}

if($data == "broadcast_forward"){
    $all_users = $users->getAllWithPrefix('');
    $MEMS = count($all_users) + ($FAKEOS ?? 0);

    bot('EditMessageText', [
        'chat_id' => $chat_id, 'message_id' => $message_id,
        'text' => "*- هەر پەیامێک (دەق، وێنە، ڤیدیۆ...) بنێرە بۆ ئەوەی فۆروارد بکرێت بۆ $MEMS بەکارهێنەر 🫡*\n",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode(['inline_keyboard' => [[["text" => "🔙 گەڕانەوە", "callback_data" => "broadcast"]]]])
    ]);
    $sessions->set('mode_' . $from_id, $data);
}

if($update->message and $sessions->get('mode_' . $from_id) == 'broadcast_forward'){
    $sessions->delete('mode_'.$from_id);
    $K = bot('SendMessage', ['chat_id' => $chat_id, 'text' => "*⏳ ئامادەکاری بۆ دەستپێکردنی فۆروارد...*",'parse_mode' => 'Markdown']);
    

    $all_users = $users->getAllWithPrefix('');
    $user_ids = array_keys($all_users);
    $MEMS = count($user_ids);
    
    $pin_enabled = ($sessions->get('pin_status_' . $from_id) == 'on');
    $ok = 0; $false = 0; $i = 0;

    foreach($user_ids as $mt){
        if(empty(trim($mt))) continue;
        $i++;
        
        $Br = br('ForwardMessage',[
            'chat_id'=>$mt,
            'from_chat_id' => $chat_id,
            'message_id'=>$update->message->message_id,
        ]);

        if($Br && $Br->ok == 1){
            $ok++;
            if($pin_enabled){
                @br('pinChatMessage', ['chat_id' => $mt, 'message_id' => $Br->result->message_id]);
            }
        }else{
            $false++;
        }
        if($i % 20 == 0 || $i == $MEMS){
            bot('EditMessageText', [
                'chat_id' => $chat_id,
                'message_id' => $K->result->message_id,
                'text' => "*ئاماری فۆروارد بۆ $MEMS 👻*
- نێردرا بۆ : $ok 
- شکستی هێنا لە ناردن : $false 
- بەرەوپێشچوون: $i / $MEMS

*لەژێر جێبەجێکردندایە ...🤗*",
                'parse_mode' => 'Markdown',
            ]);
        }
        usleep(50000);
     }
     
     bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $K->result->message_id,
        'text' => "*فۆروارد تەواو بوو بۆ $MEMS ئەندام 🙂‍↔️*
- ئەوانەی فۆرواردیان پێگەیشت : $ok 
- ئەوانەی بۆت شکستی هێنا لە ناردنی فۆروارد بۆیان : $false

*تەواو بوو 😺*",
        'parse_mode' => 'Markdown',
    ]);
}



if ($data == 'the_backup') {
    if ($from_id == ADMIN) {
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'text' => "*- بەخێربێیت بۆ بەشی نوسخەی یەدەگ 📲*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "هێنانی ڕێکخستنەکانی بۆت", "callback_data" => "getback_bot"], ["text" => "بەرزکردنەوە", "callback_data" => "uplodback_bot"]],
                    [["text" => "هێنانی هەژمارەکان", "callback_data" => "getback_acounts"], ["text" => "بەرزکردنەوە", "callback_data" => "uplodback_acounts"]],
                    [["text" => "هێنانی داواکارییەکان", "callback_data" => "getback_orders_info"], ["text" => "بەرزکردنەوە", "callback_data" => "uplodback_orders_info"]],
                    [["text" => "🔙 گەڕانەوە", "callback_data" => "BACKADMIN"]],
                ]
            ])
        ]);
    } else {
        bot('answerCallbackQuery', ['callback_query_id' => $update->callback_query->id, 'text' => "ئەم بەشە تەنها بۆ خاوەن بۆتە 🛠", 'show_alert' => true]);
    }
}

$backup_key = "thisisaverysecretkey123456789012367";

$db_map = [
    'bot' => $bot,
    'acounts' => $wallets,
    'orders_info' => $orders,
];

function encrypt_data_to_file($data_string, $output_file, $key) {
    global $bot_id, $usrbot;
    $iv = openssl_random_pseudo_bytes(openssl_cipher_iv_length('AES-256-CBC'));
    $encrypted = openssl_encrypt($data_string, 'AES-256-CBC', $key, OPENSSL_RAW_DATA, $iv);
    $file_content = "@SSFSBOT\nID: $bot_id\nUSERBOT: @$usrbot\nContenter: " . base64_encode($iv . $encrypted);
    return file_put_contents($output_file, $file_content);
}

function decrypt_file_to_data($input_file, $key) {
    $raw = @file_get_contents($input_file);
    if ($raw === false) return false;
    $data_part = explode("Contenter: ", $raw)[1] ?? '';
    if (empty($data_part)) return false;
    
    $decoded_data = base64_decode($data_part);
    $iv_length = openssl_cipher_iv_length('AES-256-CBC');
    $iv = substr($decoded_data, 0, $iv_length);
    $encrypted = substr($decoded_data, $iv_length);
    
    return openssl_decrypt($encrypted, 'AES-256-CBC', $key, OPENSSL_RAW_DATA, $iv);
}


if (preg_match('/^getback_(\w+)$/', $data, $matches) && $from_id == ADMIN) {
    $table_name = $matches[1];
    $db_object = $db_map[$table_name] ?? null;

    if ($db_object) {
        $all_data = $db_object->getAllWithPrefix('');
        $serialized_data = serialize($all_data);
        $output_file = 'backup_' . $table_name . '_' . $bot_id . '.BOT';
        
        if (encrypt_data_to_file($serialized_data, $output_file, $backup_key)) {
            bot('SendDocument', ['chat_id' => $chat_id, 'document' => new CURLFile(realpath($output_file)), 'caption' => "✅ نوسخەی یەدەگ بۆ `$table_name`"]);
            unlink($output_file);
        }
    }
}

if (preg_match('/^uplodback_(\w+)$/', $data, $matches) && $from_id == ADMIN) {
    $table_name = $matches[1];
    if (isset($db_map[$table_name])) {
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'text' => "*- فایلی نوسخەی یەدەگ بنێرە (`.BOT`) بۆ خشتەی `$table_name`*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode(['inline_keyboard' => [[["text" => "🔙 گەڕانەوە", "callback_data" => "the_backup"]]]])
        ]);
        $sessions->set('mode_' . $from_id, "UPS_CX");
        $sessions->set('HELP_' . $from_id, $table_name);
    }
}

if ($sessions->get('mode_' . $from_id) === 'UPS_CX' && isset($update->message->document)) {
    $table_to_restore = $sessions->get('HELP_' . $from_id);
    $db_object = $db_map[$table_to_restore] ?? null;
    $file_info = bot("getFile", ["file_id" => $update->message->document->file_id]);

    if ($db_object && isset($file_info->result->file_path) && pathinfo($file_info->result->file_path, PATHINFO_EXTENSION) === "BOT") {
        $download_url = "https://api.telegram.org/file/bot" . API_KEY . "/" . $file_info->result->file_path;
        $temp_file = "temp_upload_{$from_id}.BOT";
        file_put_contents($temp_file, file_get_contents($download_url));

        $decrypted_data = decrypt_file_to_data($temp_file, $backup_key);
        $restored_array = $decrypted_data ? @unserialize($decrypted_data) : false;

        if (is_array($restored_array)) {
            $db_object->clear();
            $count = 0;
            foreach ($restored_array as $k => $v) {
                $db_object->set($k, $v);
                $count++;
            }
            bot('SendMessage', ['chat_id' => $chat_id, 'text' => "*- بەرزکرایەوە و $count تۆمار گەڕێنرایەوە بۆ خشتەی `$table_to_restore` بە سەرکەوتوویی ✅*"]);
            $sessions->delete('mode_' . $from_id);
            $sessions->delete('HELP_' . $from_id);
        } else {
            bot('SendMessage', ['chat_id' => $chat_id, 'text' => "*- هەڵە: شکستی هێنا لە کردنەوەی کۆدی فایل یان فایلەکە تێکچووە ❌*"]);
        }
        unlink($temp_file);
    } else {
        bot('SendMessage', ['chat_id' => $chat_id, 'text' => "*- هەڵە: فایلەکە هەڵەیە یان خشتەی دیاریکراو بوونی نییە ❌*"]);
    }
}

if ($data == 'kshfnqat') {
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- ئایدی کەسەکە بنێرە 👤*\n",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACKADMIN"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, $data);
}

if (is_numeric($text) && $sessions->get('mode_' . $from_id) == 'kshfnqat') {
    $user_id_to_check = $text;
    $user_name = $users->get($user_id_to_check);

    if (!$user_name) {
        $user_name = "تۆمارنەکراوە";
    }

    $coins = $wallets->get('coins_' . $user_id_to_check) ?? 0;
    $coins_used = $wallets->get('coinsuseed_' . $user_id_to_check) ?? 0;
    $gift_coins = $wallets->get('hdiacoins_' . $user_id_to_check) ?? 0;
    $gift_count = $wallets->get('hdiax_' . $user_id_to_check) ?? 0;
    $transferred_out = $wallets->get('transcoins_' . $user_id_to_check) ?? 0;
    $transferred_in = $wallets->get('transsucces_' . $user_id_to_check) ?? 0;
    $referral_count = $wallets->get('countshare_' . $user_id_to_check) ?? 0;
    $referral_coins = $wallets->get('coinsshare_' . $user_id_to_check) ?? 0;

    if ($wallets->get('coins_' . $user_id_to_check) !== null) {
        $response_text = "👤 *زانیاری ئەندام:* [$user_name](tg://user?id=$user_id_to_check)\n";
        $response_text .= "🔢 *ئایدی:* `$user_id_to_check`\n\n";
        
        $response_text .= "💰 *زانیاری خاڵەکان ($a3ml):*\n";
        $response_text .= "- باڵانسی ئێستا: *$coins*\n";
        $response_text .= "- خاڵە بەکارهێنراوەکان: *$coins_used*\n\n";
        
        $response_text .= "🎁 *زانیاری دیارییەکان:*\n";
        $response_text .= "- ژمارەی دیارییە بەکارهێنراوەکان: *$gift_count*\n";
        $response_text .= "- خاڵەکان لە دیارییەکان: *$gift_coins*\n\n";
        
        $response_text .= "🔁 *زانیاری گواستنەوەکان:*\n";
        $response_text .= "- خاڵە نێردراوەکان: *$transferred_out*\n";
        $response_text .= "- خاڵە وەرگیراوەکان: *$transferred_in*\n\n";

        $response_text .= "🔗 *زانیاری بانگهێشتەکان:*\n";
        $response_text .= "- ژمارەی بانگهێشتەکان: *$referral_count*\n";
        $response_text .= "- خاڵەکان لە بانگهێشتەکان: *$referral_coins*";

        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => $response_text,
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "لابردنی خاڵەکانی ❌", "callback_data" => "nocoin_$user_id_to_check"]],
                    [["text" => "🔙 گەڕانەوە", "callback_data" => "BACKADMIN"]],
                ]
            ])
        ]);
        
        $sessions->delete('mode_' . $from_id);

    } else {
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*- ئەندام لە بۆت بوونی نییە ❌*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "🔙 گەڕانەوە", "callback_data" => "BACKADMIN"]],
                ]
            ])
        ]);
    }
}

$nocoin_ = explode("nocoin_", $data)[1];
if ($nocoin_) {
    $NQAT = $wallets->get('coins_' . $nocoin_);
    $wallets->set('coins_' . $nocoin_, 0); 
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        "message_id" => $message_id,
        'text' => "*- فەرمانی لابردن جێبەجێ کرا ✅*\n*$NQAT $a3ml* لە هەژماری `$nocoin_` لابرا و باڵانسەکەی بوو بە 0.",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACKADMIN"]],
            ]
        ])
    ]);
}

if ($data == "shtrak_jbare") {
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        "message_id" => $message_id,
        'text' => "بژاردەکانی جۆینی ناچاری:",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [['text' => "زیادکردنی کەناڵ", 'callback_data' => "add"]],
                [['text' => "پیشاندانی کەناڵەکان", 'callback_data' => "list"]],
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACKADMIN"]],
            ]
        ])
    ]);
    $forced_join->delete('mode');
}

if ($data == "add") {
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        "message_id" => $message_id,
        'text' => "یوزەری ئەو کەناڵە بنێرە کە دەتەوێت زیادی بکەیت:",
        'parse_mode' => "Markdown",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [['text' => "هەڵوەشاندنەوە ❌", 'callback_data' => "BACKADMIN"]],
            ]
        ])
    ]);
    $forced_join->set('mode', 'add_channel');
}

if ($forced_join->get('mode') == 'add_channel' && isset($text) && strpos($text, '@') === 0) {
    $channel_info = bot('getChat', ['chat_id' => $text]);
    $channel_data = json_decode(json_encode($channel_info), true);

    if ($channel_data['ok'] ) {
        $member_info = bot('getChatMember', ['chat_id' => $text, 'user_id' => $bot_id]);
        $member_data = json_decode(json_encode($member_info), true);

        if ($member_data['ok'] && in_array($member_data['result']['status'], ['administrator', 'creator'])) {
            $channels = $forced_join->get('channels') ?: [];
            if (!in_array($text, $channels)) {
                $channels[] = $text;
                $forced_join->set('channels', $channels);
                $forced_join->delete('mode');

                bot('sendMessage', [
                    'chat_id' => $chat_id,
                    'text' => "✅ کەناڵەکە بە سەرکەوتوویی زیادکرا:\n\n$text",
                    'reply_markup' => json_encode([
                        'inline_keyboard' => [
                            [['text' => "🔙 گەڕانەوە", 'callback_data' => "list"]],
                        ]
                    ])
                ]);
            } else {
                bot('sendMessage', [
                    'chat_id' => $chat_id,
                    'text' => "❌ کەناڵەکە پێشتر زیادکراوە:\n\n$text",
                ]);
            }
        } else {
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => "❌ بۆتەکە ئەدمین نییە لە کەناڵەکە:\n\n$text",
            ]);
        }
    } else {
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => "❌ کەناڵەکە بوونی نییە یان کەناڵێکی گشتی نییە:\n\n$text",
        ]);
    }
}
if ($data == "list") {
    $channels = $forced_join->get('channels') ?: [];

    if (!empty($channels)) {
        $keyboard = [];
        foreach ($channels as $index => $channel) {
            $keyboard[] = [
                ['text' => "$channel", 'url' => "https://t.me/" . ltrim($channel, '@')],
                ['text' => "زانیاری 👤", 'callback_data' => "INFCH_$index"]
            ];
        }
        $keyboard[] = [['text' => "🔙 گەڕانەوە", 'callback_data' => "BACKADMIN"]];

        bot('EditMessageText', [
            'chat_id' => $chat_id,
            "message_id" => $message_id,
            'text' => "📋 کەناڵە زیادکراوەکان بۆ جۆینی ناچاری:",
            'reply_markup' => json_encode(['inline_keyboard' => $keyboard]),
        ]);
    } else {
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            "message_id" => $message_id,
            'text' => "❌ هیچ کەناڵێک زیاد نەکراوە.",
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [['text' => "🔙 گەڕانەوە", 'callback_data' => "BACKADMIN"]],
                ]
            ])
        ]);
    }
}

if (strpos($data, "INFCH_") === 0) {
    $index = (int) str_replace("INFCH_", "", $data);
    $channels = $forced_join->get('channels') ?: [];

    if (isset($channels[$index])) {
        if($forced_join->get("channel_count_$index")){
            $d = $forced_join->get("channel_count_$index");
            $J = "- ژمارەی داواکراو بۆ چوونەژوورەوە : $d";
            $d = $join_tracker->get("channel_count_$index") ?? 0;
            $H = "- $d چوونەتە ژوورەوە";
        }
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            "message_id" => $message_id,
            'parse_mode' => 'Markdown',
            'text' => "- زانیاری کەناڵ : [" . $channels[$index] . "] ✅
$J
$H",
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [['text' => "سڕینەوەی کەناڵ ❌", 'callback_data' => "delete_$index"]],
                    [['text' => "دیاریکردنی ژمارەی چوونەژوورەوە", 'callback_data' => "tachch_$index"]],
                    [['text' => "🔙 گەڕانەوە", 'callback_data' => "list"]],
                ]
            ])
        ]);
    } else {
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            "message_id" => $message_id,
            'text' => "⚠️ کەناڵی داواکراو نەدۆزرایەوە.",
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [['text' => "🔙 گەڕانەوە", 'callback_data' => "list"]],
                ]
            ])
        ]);
    }
}

if (strpos($data, "tachch_") === 0) {
    $index = str_replace("tachch_", "", $data);
    $channels = $forced_join->get('channels') ?: [];

    if (isset($channels[$index])) {
        $forced_join->set("set_count_channel", $index);

        bot('EditMessageText', [
            'chat_id' => $chat_id,
            "message_id" => $message_id,
            'text' => "🧮 ئێستا ژمارەی چوونەژوورەوەی داواکراو بۆ کەناڵەکە بنێرە:\n[" . $channels[$index] . "]",
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [['text' => "هەڵوەشاندنەوە ❌", 'callback_data' => "list"]],
                ]
            ])
        ]);
        $forced_join->set('DATA', $index);
        $forced_join->set('mode', 'edit_3dd_ch');
        return;
    } else {
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "❌ کەناڵەکە بوونی نییە.",
        ]);
    }
}

$index = $forced_join->get("set_count_channel");

if (is_numeric($text) && $index !== null) {
    $channels = $forced_join->get('channels') ?: [];

    if (isset($channels[$index])) {
        $forced_join->set("channel_count_$index", $text);

        $forced_join->set("set_count_channel", null);

        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "✅ ژمارەی چوونەژوورەوە [$text] دیاریکرا بۆ کەناڵەکە:\n" . $channels[$index],
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [['text' => "🔙 گەڕانەوە", 'callback_data' => "list"]],
                ]
            ])
        ]);
    }
}



if (strpos($data, "delete_") === 0) {
    $index = str_replace("delete_", "", $data);
    $channels = $forced_join->get('channels') ?: [];

    if (isset($channels[$index])) {
        $deleted_channel = $channels[$index];
        unset($channels[$index]);
        $channels = array_values($channels);
        $forced_join->set('channels', $channels);
        $forced_join->delete("channel_count_$index");
$join_tracker->delete("channel_count_$index");
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            "message_id" => $message_id,
            'text' => "✅ کەناڵەکە سڕایەوە:\n\n$deleted_channel",
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [['text' => "🔙 گەڕانەوە", 'callback_data' => "list"]],
                ]
            ])
        ]);
    } else {
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            "message_id" => $message_id,
            'text' => "❌ هەڵەیەک ڕوویدا. کەناڵەکە بوونی نییە.",
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [['text' => "🔙 گەڕانەوە", 'callback_data' => "list"]],
                ]
            ])
        ]);
    }
}




$tgle_ = explode("tgle_",$data)[1];
if($tgle_){
$now_mode = $bot->get('generals_'. $tgle_);
if($now_mode != '✅'){
    $bot->set('generals_'. $tgle_ , '✅');
}else{
    $bot->set('generals_'. $tgle_ , '❌');
}
$data = "Al_aqsam_1";
}


if ($data == 'RESET_START_MSG') {
    $bot->delete('START_');
    bot('answerCallbackQuery', [
        'callback_query_id' => $update->callback_query->id,
        'text' => 'پەیامی بنەڕەتی بە سەرکەوتوویی گەڕێندرایەوە.',
        'show_alert' => true
    ]);
    $data = 'al_START';
}

if($data == "al_START"){
    $NOW_STA =  $bot->get('START_');
    if(!$NOW_STA){
        $NOW_STA = "پەیامی بنەڕەتی (هیچ دەقێکی تایبەت نییە)";
    }
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*- بەشی پەیامی بەخێرهاتن (/start) .*\n ⌯ ئێستا: `$NOW_STA`",
        'parse_mode' => 'Markdown', 
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "دیاریکردنی پەیام", "callback_data" => "SET_TH_START"]],
                [["text" => "گەڕاندنەوەی پەیامی بنەڕەتی", "callback_data" => "RESET_START_MSG"]],
                [["text" => "گەڕانەوە", "callback_data" => "BACKADMIN"]],
            ]
        ])
    ]);
}

if($data=='SET_TH_START'){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*- پەیامی بەخێرهاتن بنێرە ئێستا :*\n (⌯ ئەو هاشتاگانەی ڕێگەت پێدراوە بەکاریان بهێنیت.)\n - `#a` - *بۆ دانانی ناوی بەکارهێنەر و تێیدا بەستەری هەژمار*\n - `#b` - *بۆ دانانی ناوی هەژمار*\n - `#c` - *بۆ دانانی ئایدی هەژمار*\n - `#d` - *بۆ دانانی یوزەری بەکارهێنەر*\n - `#e` - *بۆ دانانی ژمارەی $a3ml*",
        'parse_mode' => 'Markdown', 
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "al_START"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id , $data);
    return;
}

if($text and $sessions->get('mode_'.$from_id) == "SET_TH_START"){
    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => "*- پەیامی بەخێرهاتن پاشەکەوت کرا .*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "al_START"]]
            ]
        ])
    ]);
    $TH_START = str_replace(array('#a','#b' , '#c' , '#d' , '#e') , array("[$name](tg://user?id=$from_id)" ,"$name" , "$from_id" , "[$username]" ,$wallets->get('coins_'.$chat_id)) , $text);
    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => "*- نموونەیەک بۆ پەیامی بەخێرهاتن.*\n$TH_START",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "al_START"]]
            ]
        ])
    ]);

    $bot->set('START_', "$text");
    $sessions->delete('mode_'.$from_id);
}

if($data == 'BACKADMIN'){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "~ بەخێربێیت بۆ پانێڵی ئەدمینی بۆت 🤖
~ دەتوانیت هەموو فەرمانەکانی بۆت لەم بەشە کۆنترۆڵ بکەیت",
        'parse_mode' => 'Markdown', 
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "چاکسازی : ".$bot->get('generals_siana'), "callback_data" => "tgle_siana"],
["text" => "ئاگاداری هاتن : ".$bot->get('generals_entry'), "callback_data" => "tgle_entry"]],
                [["text" => "نامەی بەخێرهاتن ( /start )", "callback_data" => "al_START"]],
                [["text" => "پاراستنی بۆت", "callback_data" => "ALHMAIA"],["text" => "بلۆککردن", "callback_data" => "BLOCKS"]],
                [["text" => "دوگمە شەفافەکان", "callback_data" => "AL_AZRAR"],
                ["text" => "فەرمانە کورتکراوەکان", "callback_data" => "al_commands"]],
                [["text" => "جۆینی ناچاری", "callback_data" => "shtrak_jbare"],
["text" => "ناردنی گشتی", "callback_data" => "broadcast"]],
[["text" => "ئامارەکان", "callback_data" => "ADMIN_STATS"],
['text' => 'ئەدمینەکان', 'callback_data' => 'ADMINS']],
                [["text" => "ڕێکخستنەکانی بۆت", "callback_data" => "SETTINGER"]],                
            [["text" => "گەڕانەوە بۆ دۆخی بەکارهێنەر", "callback_data" => "BACK"]],
            ]
        ])
    ]);
    $sessions->delete('mode_'.$from_id);
    $sessions->delete('help_'.$from_id);
}

if($data == 'Al_aqsam_1'){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "~ بەخێربێیت بۆ پانێڵی ئەدمینی بۆت 🤖
~ دەتوانیت هەموو فەرمانەکانی بۆت لەم بەشە کۆنترۆڵ بکەیت",
        'parse_mode' => 'Markdown', 
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "چاکسازی : ".$bot->get('generals_siana'), "callback_data" => "tgle_siana"],
["text" => "ئاگاداری هاتن : ".$bot->get('generals_entry'), "callback_data" => "tgle_entry"]],
                [["text" => "نامەی بەخێرهاتن ( /start )", "callback_data" => "al_START"]],
                [["text" => "پاراستنی بۆت", "callback_data" => "ALHMAIA"],["text" => "بلۆککردن", "callback_data" => "BLOCKS"]],
                [["text" => "دوگمە شەفافەکان", "callback_data" => "AL_AZRAR"],
                ["text" => "فەرمانە کورتکراوەکان", "callback_data" => "al_commands"]],
                [["text" => "جۆینی ناچاری", "callback_data" => "shtrak_jbare"],
["text" => "ناردنی گشتی", "callback_data" => "broadcast"]],
[["text" => "ئامارەکان", "callback_data" => "ADMIN_STATS"],
['text' => 'ئەدمینەکان', 'callback_data' => 'ADMINS']],
                [["text" => "ڕێکخستنەکانی بۆت", "callback_data" => "SETTINGER"]],
            [["text" => "گەڕانەوە بۆ دۆخی بەکارهێنەر", "callback_data" => "BACK"]],
            ]
        ])
    ]);
}


if ($data == "ADMIN_STATS") {
    $all_users_from_db = $users->getAllWithPrefix('');
    $total_users = count($all_users_from_db);
    $all_accounts_data = $wallets->getAllWithPrefix(''); 

    $total_points_system = 0;
    $total_points_spent = 0;
    $total_from_gifts = 0;
    $total_from_referrals = 0;

    foreach ($all_accounts_data as $key => $value) {
        if (strpos($key, 'coins_') === 0) {
            $total_points_system += (int)$value;
        } elseif (strpos($key, 'coinsuseed_') === 0) {
            $total_points_spent += (int)$value;
        } elseif (strpos($key, 'hdiacoins_') === 0) {
            $total_from_gifts += (int)$value;
        } elseif (strpos($key, 'coinsshare_') === 0) {
            $total_from_referrals += (int)$value;
        }
    }

    $active_now_count = 0;
    $time_frame = 300;
    $all_cache_data = $cache->getAllWithPrefix('last_active_');
    foreach ($all_cache_data as $key => $last_active_time) {
        if ($last_active_time && (time() - $last_active_time) <= $time_frame) {
            $active_now_count++;
        }
    }

    $active_today = (int)$stats->get('activers_today');
    $active_month = (int)$stats->get('activers_MONTH');
    $blocked_users = count($bot->get("blocks") ?? []);
    $total_orders = (int)$bot->get('ORDERS') ?? 0;
    $funding_channels = count(array_filter(explode("\n", $funding->get("IDXS"))));

    $formatted_total_users = number_format($total_users);
    $formatted_active_now = number_format($active_now_count);
    $formatted_active_today = number_format($active_today);
    $formatted_active_month = number_format($active_month);
    $formatted_blocked_users = number_format($blocked_users);
    $formatted_total_points = number_format($total_points_system);
    $formatted_total_spent = number_format($total_points_spent);
    $formatted_total_gifts = number_format($total_from_gifts);
    $formatted_total_referrals = number_format($total_from_referrals);
    $formatted_total_orders = number_format($total_orders);
    $formatted_funding_channels = number_format($funding_channels);

    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "📊 *ئامارەکانی بۆت*\n\n" .
                  "*• ئاماری بەکارهێنەران:*\n" .
                  "- کۆی گشتی بەکارهێنەران: *$formatted_total_users*\n" .
                  "- بەکارهێنەرە چالاکەکان ئێستا: *$formatted_active_now*\n" .
                  "- بەکارهێنەرە چالاکەکانی ئەمڕۆ: *$formatted_active_today*\n" .
                  "- بەکارهێنەرە چالاکەکانی ئەم مانگە: *$formatted_active_month*\n" .
                  "- بەکارهێنەرە بلۆککراوەکان: *$formatted_blocked_users*\n\n" .
                  
                  "*• ئاماری {$a3ml}:*\n" .
                  "- کۆی گشتی {$a3ml} بەردەست: *$formatted_total_points*\n" .
                  "- کۆی گشتی {$a3ml} خەرجکراو: *$formatted_total_spent*\n" .
                  "- کۆی گشتی {$a3ml} لە دیاری و کۆدەکان: *$formatted_total_gifts*\n" .
                  "- کۆی گشتی {$a3ml} لە بانگهێشتکردن: *$formatted_total_referrals*\n\n" .

                  "*• ئاماری چالاکی:*\n" .
                  "- کۆی گشتی داواکارییە تەواوبووەکان: *$formatted_total_orders*\n" .
                  "- کەناڵەکان لە پڕۆسەی زیادکردن ئەندام: *$formatted_funding_channels*",
        'parse_mode' => 'Markdown',
        'disable_web_page_preview' => true,
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACKADMIN"]],
            ]
        ])
    ]);
}

if($data == 'asasse'){
    $DOMIN = $bot->get('GENERALS_DOMIN') ?? "نییە !";
    $KEY = $bot->get('GENERALS_KEY') ?? "نییە !";
    $cost = json_decode(file_get_contents("https://$DOMIN/api/v2?key=$KEY&action=balance"), 1);
    $balance = $cost['balance'];
    $currency = $cost['currency'];
    if($balance){
        $HH = "- باڵانسی بەردەست : `$balance`";
    }else{
        $HH = "\n*زانیاری هەڵە ([API_KEY] یان [DOMAIN])*";
    }
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
       'text' => "*- بەخێربێیت بۆ بەشی بەستنەوە سەرەکییەکان *
- دۆمەینی دانراو : `$DOMIN`
- کلیل : `$KEY`
$HH

*- ئەم بەشە دروستکراوە تەنها بۆ بەستنەوەی دەرەکی، واتە دەتوانیت خزمەتگوزاری زیادکراو ببەستیتەوە بەم زانیارییە ئامادەکراوانە ئەگەر بتەوێت !*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "دیاریکردنی دۆمەین", "callback_data" => "SRTGENERAL_DOMIN"]],
                [["text" => "دیاریکردنی کلیل [API_KEY]", "callback_data" => "SRTGENERAL_KEY"]],
                [["text" => "بەشی بەستنەوە فرەییەکان", "callback_data" => "multi_rbts"]],
                [["text" => "گەڕانەوە", "callback_data" => "BACKADMIN"]],
            ]
        ])
    ]);
    $sessions->delete('mode_'.$from_id);
    $sessions->delete('help_'.$from_id);
}
if(preg_match("/^DELETERBT_(\d+)$/", $data, $match)){
    $index = $match[1];
    $all_rbts = explode("\n", trim($bot->get('OTHER_RBTS')));
    
    if(isset($all_rbts[$index])){
        unset($all_rbts[$index]);
        $all_rbts = array_values($all_rbts);
        $bot->set('OTHER_RBTS', implode("\n", $all_rbts));
    }

    $data = 'multi_rbts';
}

if($data == 'multi_rbts'){
    $DOMx = [];
    $i = 0;
    $other_rbts = explode("\n", trim($bot->get('OTHER_RBTS')));
    foreach($other_rbts as $RBTS){
        if(empty($RBTS)) continue; 
        $texts = explode("|", $RBTS);
        $DOMAIN = $texts[0] ?? '';
        $KEY = $texts[1] ?? '';
        $DOMx[] = [
            ["text" => "$DOMAIN", "url" => "https://$DOMAIN"],
            ["text" => "❌ سڕینەوە", "callback_data" => "DELETERBT_$i"]
        ];
        $i++;
    }

    $DOMx[] = [["text" => "➕ زیادکردنی بەستنەوە", "callback_data" => "ADDNEW_RBT"]];
    $DOMx[] = [["text" => "گەڕانەوە", "callback_data" => "asasse"]];

    $rbts = count(array_filter($other_rbts)); 
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*- بەشی بەستنەوە فرەییەکان 🔠 *
- ژمارەی بەستنەوەکانی ئێستا : `$rbts`
- کۆی گشتی باڵانسی بەردەست : `$ijmale`

*- ئەم بەشە دروستکراوە تەنها بۆ بەستنەوەی دەرەکی، واتە دەتوانیت خزمەتگوزاری زیادکراو ببەستیتەوە بەم زانیارییە ئامادەکراوانە ئەگەر بتەوێت !*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode(["inline_keyboard" => $DOMx])
    ]);

    $sessions->delete('mode_'.$from_id);
    $sessions->delete('help_'.$from_id);
}


if($data == 'ADDNEW_RBT'){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
       'text' => "*- بەستنەوە نوێیەکان بەم شێوەیە بنێرە ئێستا*
[DOMAIN|API_KEY]

- نموونە : `example.com|KEY12347899009`
- دەتوانیت زیاتر لە یەک بەستنەوە بنێریت
",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "multi_rbts"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id , $data);
    return;
}

if($text and $sessions->get('mode_'.$from_id) == "ADDNEW_RBT"){
    $texts = explode("|", $text)[1];
    if($texts[0] and $texts[1]){
    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => "*- بەستنەوەکە زیادکرا بۆ لیستی بەستنەوەکان ✅*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                
                [["text" => "🔙 گەڕانەوە", "callback_data" => "multi_rbts"]]
            ]
        ])
    ]);
    $bot->set('OTHER_RBTS', $bot->get('OTHER_RBTS') ."\n$text");
}else{
    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => "*- هەڵە لە شێواز، تکایە بە شێوازی داواکراو بنێرە ❌*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                
                [["text" => "🔙 گەڕانەوە", "callback_data" => "multi_rbts"]]
            ]
        ])
    ]);
}
    $sessions->delete('mode_'.$from_id);
    $sessions->delete('help_'.$from_id);
}


if (strpos($data, "confirm_delete_qsm_") === 0) {
    $qsm_id = str_replace("confirm_delete_qsm_", "", $data);
    $qsm_name = $bot->get('qsms_name_' . $qsm_id);

    if ($qsm_name) {
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'text' => "🚨 *ئایا دڵنیایت لە سڕینەوەی بەشی '$qsm_name'؟*\n\nبەشەکە و *هەموو خزمەتگوزارییەکان*ی ناوی بە یەکجاری دەسڕێنەوە. ناتوانرێت ئەم کردارە هەڵبوەشێندرێتەوە.",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [
                        ['text' => "✅ بەڵێ، بیسڕەوە", 'callback_data' => "deleteqsm_$qsm_id"],
                        ['text' => "❌ نەخێر، هەڵوەشاندنەوە", 'callback_data' => "ENTERQSM_$qsm_id"] 
                    ]
                ]
            ])
        ]);
    }
}

if (strpos($data, "deleteqsm_") === 0) {
    $qsm_id_to_delete = str_replace("deleteqsm_", "", $data);
   
    $qsm_name_to_delete = $bot->get('qsms_name_' . $qsm_id_to_delete);

    if ($qsm_name_to_delete) {

        $services_list_string = $bot->get('xdmat_' . $qsm_id_to_delete);
        if ($services_list_string) {
            $services_list_array = explode("\n", $services_list_string);

            foreach ($services_list_array as $service_name) {
                $service_name = trim($service_name);
                if (empty($service_name)) continue;

                $service_id = $bot->get('xdmat_' . $service_name);
                if ($service_id) {
                    $bot->delete('XDMA_INF_DOMIN__' . $service_id);
                    $bot->delete('XDMA_INF_KEY__' . $service_id);
                    $bot->delete('XDMA_INF_MIN__' . $service_id);
                    $bot->delete('XDMA_INF_MAX__' . $service_id);
                    $bot->delete('XDMA_INF_PRICE__' . $service_id);
                    $bot->delete('XDMA_INF_ID__' . $service_id);
                    $bot->delete('XDMA_INF_DESCRIPTION__' . $service_id);
                    $bot->delete('XDMA_INF_TSLEM__' . $service_id);
                    
                    $bot->delete('xdmatname_' . $service_id);
                    $bot->delete('xdmatinqsm_' . $service_id);
                    $bot->delete('xdmat_' . $service_name);
                }
            }
        }

        $bot->delete('xdmat_' . $qsm_id_to_delete);
        $bot->delete('qsms_name_' . $qsm_id_to_delete);
        $bot->delete('qsms_id_' . $qsm_name_to_delete);
        $bot->delete('qsm_status_' . $qsm_id_to_delete); 

        $all_qsms_string = $bot->get('qsms');
        $all_qsms_array = explode("\n", $all_qsms_string);
        
        $new_qsms_array = array_filter($all_qsms_array, function($current_qsm_name) use ($qsm_name_to_delete) {
            return trim($current_qsm_name) !== trim($qsm_name_to_delete);
        });

        $new_qsms_string = implode("\n", $new_qsms_array);
        $bot->set('qsms', $new_qsms_string);
        
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'text' => "*✅ بەشی '$qsm_name_to_delete' و هەموو خزمەتگوزارییەکانی بە سەرکەوتوویی سڕانەوە.*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [['text' => '🔙 گەڕانەوە', 'callback_data' => 'xdmats']]
                ]
            ])
        ]);
        
        return; 
    }
}


$deletexdma_ = explode("deletexdma_",$data)[1];
if($deletexdma_){
    $service_id_to_delete = $deletexdma_;
    $qsm = $bot->get('xdmatinqsm_'.$service_id_to_delete);
    $name_xdma_to_delete = $bot->get('xdmatname_' . $service_id_to_delete);

    if ($qsm && $name_xdma_to_delete) {
        $current_services_string = $bot->get('xdmat_'.$qsm);
        $services_array = explode("\n", $current_services_string);
        $new_services_array = array_filter($services_array, function($service_name) use ($name_xdma_to_delete) {
            return trim($service_name) !== trim($name_xdma_to_delete);
        });
        $new_services_string = implode("\n", $new_services_array);
        $bot->set('xdmat_'.$qsm, $new_services_string);

        $bot->delete('XDMA_INF_DOMIN__' . $service_id_to_delete);
        $bot->delete('XDMA_INF_KEY__' . $service_id_to_delete);
        $bot->delete('XDMA_INF_MIN__' . $service_id_to_delete);
        $bot->delete('XDMA_INF_MAX__' . $service_id_to_delete);
        $bot->delete('XDMA_INF_PRICE__' . $service_id_to_delete);
        $bot->delete('XDMA_INF_ID__' . $service_id_to_delete);
        $bot->delete('XDMA_INF_DESCRIPTION__' . $service_id_to_delete);
        $bot->delete('XDMA_INF_TSLEM__' . $service_id_to_delete);
        
        $bot->delete('xdmatinqsm_'.$service_id_to_delete);
        $bot->delete('xdmatname_' . $service_id_to_delete);
        $bot->delete('xdmat_' . $name_xdma_to_delete);
    }
    $data = "ENTERQSM_$qsm";
}

if (strpos($data, "toggle_qsm_status_") === 0) {
    $qsm_id = str_replace("toggle_qsm_status_", "", $data);
    
    $current_status = $bot->get('qsm_status_' . $qsm_id) ?? '✅';
    $new_status = ($current_status == '✅') ? '❌' : '✅';
    $bot->set('qsm_status_' . $qsm_id, $new_status);
    
    $data = "ENTERQSM_$qsm_id"; 
}


$names_ = explode("names_", $data)[1];
if($names_){
    $qsm_id = $names_;
    $qsm_name = $bot->get('qsms_name_' . $qsm_id);

    $xdmat_list_str = $bot->get('xdmat_' . $qsm_id);
    
    if(empty(trim($xdmat_list_str))){
        bot('answerCallbackQuery', [
            'callback_query_id' => $update->callback_query->id,
            'text' => "❌ هیچ خزمەتگوزارییەک لەم بەشەدا نییە!",
            'show_alert' => true
        ]);
    } else {
        $services_array = explode("\n", $xdmat_list_str);
        $output_text = "--- لیستی خزمەتگوزارییەکانی بەشی: $qsm_name ---\n\n";
        $count = 0;

        foreach($services_array as $service_name){
            $service_name = trim($service_name);
            if(empty($service_name)) continue;

            $service_idx = $bot->get('xdmat_' . $service_name);
            $api_id = $bot->get('XDMA_INF_ID__' . $service_idx) ?? "دیاری نەکراوە";
            $price = $bot->get('XDMA_INF_PRICE__' . $service_idx) ?? "دیاری نەکراوە";
            
            $count++;
            $output_text .= "$count- ناوی خزمەتگوزاری: $service_name\n";
            $output_text .= "   ئایدی لە سایت: $api_id\n";
            $output_text .= "   نرخ: $price\n";
            $output_text .= "-----------------------------------\n";
        }

        $filename = "services_list_" . $qsm_id . ".txt";
        file_put_contents($filename, $output_text);

        bot('sendDocument', [
            'chat_id' => $chat_id,
            'document' => new CURLFile(realpath($filename)),
            'caption' => "✅ *لیستی خزمەتگوزارییەکان*\n📂 بەشی: `$qsm_name`\n🔢 ژمارەی خزمەتگوزاری: `$count`",
            'parse_mode' => 'Markdown'
        ]);
        unlink($filename);
    }
}


if ($data == 'xdmats') {
    $S_LIST = ['inline_keyboard' => []];
    $qsms_list = explode("\n", $bot->get('qsms'));

    foreach ($qsms_list as $qsms) {
        $qsms = trim($qsms);
        if (!empty($qsms)) {
            $idx = $bot->get('qsms_id_' . $qsms);
            if(!$idx){
                $idx = coderandom(10);
                $bot->set('qsms_id_'.$qsms,$idx);
                $bot->set('qsms_name_'.$idx,$qsms);
            }
            if(!empty($bot->get('qsms_name_'.$idx))){

                $S_LIST['inline_keyboard'][] = [
                    ['text' => "$qsms", 'callback_data' => "ENTERQSM_$idx"]
                ];
            }
        }
    }

    $S_LIST['inline_keyboard'][] = [['text' => "زیادکردنی بەش ➕", 'callback_data' => "addqsm"]];
    $S_LIST['inline_keyboard'][] = [['text' => "🔙 گەڕانەوە", 'callback_data' => "BACKADMIN"]];

    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- بەڕێوەبردنی خزمەتگوزارییەکان و بەشەکان*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode($S_LIST)
    ]);
    $sessions->delete('mode_'.$from_id);
    $sessions->delete('help_'.$from_id);
}


if($data == 'rename_qsm'){
    $qsms_list = explode("\n", $bot->get('qsms'));
    $buttons = [];
    foreach ($qsms_list as $qsm_name) {
        $qsm_name = trim($qsm_name);
        if (!empty($qsm_name)) {
            $qsm_id = $bot->get('qsms_id_' . $qsm_name);
            if ($qsm_id) {
                $buttons[] = [['text' => $qsm_name, 'callback_data' => "ask_new_name_for_".$qsm_id]];
            }
        }
    }
    $buttons[] = [['text' => "🔙 گەڕانەوە", 'callback_data' => "xdmats"]];
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "✏️ *ئەو بەشە هەڵبژێرە کە دەتەوێت ناوەکەی بگۆڕیت:*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
        'inline_keyboard' => $buttons])
    ]);
    $sessions->delete('mode_'.$from_id);
}

if(strpos($data, "ask_new_name_for_") === 0){
    $qsm_id = str_replace("ask_new_name_for_", "", $data);
    $current_name = $bot->get('qsms_name_' . $qsm_id);
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*ئێستا ناوی نوێ بۆ بەشەکە بنێرە:* `$current_name`", 
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
        'inline_keyboard' => [
            [['text' => "🔙 گەڕانەوە", 'callback_data' => "ENTERQSM_$qsm_id"]] 
        ]])
    ]);
    $sessions->set('mode_' . $from_id, 'set_new_qsm_name');
    $sessions->set('helper_' . $from_id, $qsm_id);
}

if($text and $sessions->get('mode_' . $from_id) == 'set_new_qsm_name'){
    $new_name = trim($text);
    $qsm_id = $sessions->get('helper_' . $from_id);
    if($qsm_id){
        $old_name = $bot->get('qsms_name_' . $qsm_id);
        $all_qsms_string = $bot->get('qsms');
        $bot->set('qsms', str_replace($old_name, $new_name, $all_qsms_string));

        $bot->set('qsms_name_' . $qsm_id, $new_name);
        
        $bot->delete('qsms_id_' . $old_name);
        $bot->set('qsms_id_' . $new_name, $qsm_id);

        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => "*✅ ناوی بەشەکە بە سەرکەوتوویی گۆڕدرا لە `$old_name` بۆ `$new_name`.*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [['text' => '🔙 گەڕانەوە', 'callback_data' => "ENTERQSM_$qsm_id"]] 
                ]
            ])
        ]);
        $sessions->delete('mode_' . $from_id);
        $sessions->delete('helper_' . $from_id);
    }
}

$SRTGENERAL_ = explode("SRTGENERAL_", $data)[1];
if($SRTGENERAL_){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*- *[$SRTGENERAL_] *ئێستا بنێرە :*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                
                [["text" => "🔙 گەڕانەوە", "callback_data" => "asasse"]]
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, 'editgeneral');
    $sessions->set('help_' . $from_id, $SRTGENERAL_);

}

if($sessions->get('mode_'.$from_id) == 'editgeneral' && $text){
    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => "*بە سەرکەوتوویی دیاریکرا *",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                
                [["text" => "🔙 گەڕانەوە", "callback_data" => "asasse"]]
            ]
        ])
    ]);
    $bot->set('GENERALS_'. $sessions->get('help_' . $from_id) , $text);
    $sessions->delete('mode_'.$from_id);
    $sessions->delete('help_'.$from_id);
}

$OTHERRBTS_ = explode('OTHERRBTS_',$data)[1];
if($OTHERRBTS_){
    $in = $bot->get("xdmatinqsm_".$OTHERRBTS_);
    $name_xdma = $bot->get('xdmatname_' . $OTHERRBTS_) ?? '0';
    $DOMx = [];
    $i = 0;
    $other_rbts = explode("\n", trim($bot->get('OTHER_RBTS')));
    foreach($other_rbts as $RBTS){
        if(empty($RBTS)) continue; 
        $texts = explode("|", $RBTS);
        $DOMAIN = $texts[0] ?? '';
        $KEY = $texts[1] ?? '';
        $DOMx[] = [
            ["text" => "$DOMAIN", "url" => "https://$DOMAIN"],
            ["text" => "ببەستە", "callback_data" => "CONNECTRBT_".$i]
        ];
        $i++;
    }
    if($i < 1){
        bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*- هیچ بەستنەوەیەک زیاد نەکراوە*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "بەشی بەستنەوەکان", "callback_data" => "multi_rbts"]],
                [["text" => "🔙 گەڕانەوە", "callback_data" => "ENTERXDMA_$OTHERRBTS_"]]
            ]
        ])
    ]);
    }else{
        $DOMx[] = [["text" => "🔙 گەڕانەوە", "callback_data" => "ENTERXDMA_$OTHERRBTS_"]];
        bot('EditMessageText', [
            'chat_id' => $chat_id, 
            'message_id' => $message_id,
            'text' => "*- خزمەتگوزاری $name_xdma ئەوە هەڵبژێرە کە پێت باشە بیبەستیتەوە*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode(["inline_keyboard" => $DOMx])
        ]);
        $sessions->set('help_'.$from_id , $OTHERRBTS_);
    }
}
$CONNECTRBT_ = explode('CONNECTRBT_', $data)[1];
if ($CONNECTRBT_ !== null && $CONNECTRBT_ !== '') {
    $in = $bot->get("xdmatinqsm_" . $sessions->get('help_' . $from_id));
    $name_xdma = $bot->get('xdmatname_' . $sessions->get('help_' . $from_id)) ?? '0';
    $index = $CONNECTRBT_;
    $all_rbts = explode("\n", trim($bot->get('OTHER_RBTS')));
    if (isset($all_rbts[$index])) {
        $D = explode('|', $all_rbts[$index]);
        $DOMAIN = $D[0];
        $KEY = $D[1];
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'text' => "*- خزمەتگوزاری $name_xdma بەستراوە بە $DOMAIN*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "🔙 گەڕانەوە", "callback_data" => "OTHERRBTS_" . $sessions->get('help_' . $from_id)]]
                ]
            ])
        ]);
        $bot->set('XDMATSOTHER_'. $sessions->get('help_' . $from_id) , $all_rbts[$index]);
    }
}

$toggle_service_ = explode("toggle_service_" , $data)[1];
if($toggle_service_){
    $ID_XDMA = $toggle_service_;
    $X = $bot->get('service_status_' . $ID_XDMA);
    if($X == '❌'){
        $status = "✅";
    }else{
        $status = "❌";
    }
    $bot->set('service_status_' . $ID_XDMA , $status);
    $data = "ENTERXDMA_$ID_XDMA";
}

$TSLEMER_ = explode("TSLEMER_" , $data)[1];
if($TSLEMER_){
    $ID_XDMA = $TSLEMER_;
    $X = $bot->get('XDMA_INF_TSLEM__'. $ID_XDMA);
    if($X == 'دەستی'){
        $سوي = "ئۆتۆماتیکی";
    }else{
        $سوي = "دەستی";
    }
    $bot->set('XDMA_INF_TSLEM__'. $ID_XDMA , $سوي);
    $data = "ENTERXDMA_$ID_XDMA";
}
$ENTERXDMA_ = explode("ENTERXDMA_", $data)[1] ?? null;

if ($ENTERXDMA_) {
    $ID_XDMA = $ENTERXDMA_;
    $in = $bot->get("xdmatinqsm_".$ENTERXDMA_);
    $name_xdma = $bot->get('xdmatname_' . $ENTERXDMA_) ?? '0';
    $status_now = $bot->get('service_status_' . $ID_XDMA) ?? '✅';
    
    $infoos = $bot->get('infos_' . $ENTERXDMA_) ?? '0';
    

        $S_TEXT = explode('|', $infoos);
        list($DOMIN, $API, $ID, $MAX, $MIN, $PRICE , $description) = array_pad($S_TEXT, 6, 'N/A');
        if($bot->get('GENERALS_DOMIN') and $bot->get('GENERALS_KEY')){
            $DOMINx = $bot->get('GENERALS_DOMIN');
            $YOU_CAN = "ببەستە بە - $DOMINx (ئارەزوومەندانە)";
        }
        if($bot->get("GENERALS_DOMINX_". $ENTERXDMA_)){
        $DOMIN = $bot->get('GENERALS_DOMIN');
        $API = $bot->get('GENERALS_KEY');
        $YOU_CAN = "هەڵوەشاندنەوە لەگەڵ - $DOMIN .";
    }
    if($bot->get('XDMATSOTHER_'. $ENTERXDMA_)){
        $DOMIN = explode('|',$bot->get('XDMATSOTHER_'. $ENTERXDMA_))[0];
        $API = explode('|',$bot->get('XDMATSOTHER_'. $ENTERXDMA_))[1];
    }
    $DOMIN = $bot->get('XDMA_INF_DOMIN__'. $ID_XDMA) ?? "دانەنراوە";
    $API = $bot->get('XDMA_INF_KEY__'. $ID_XDMA) ?? "دانەنراوە";
    $MIN = $bot->get('XDMA_INF_MIN__'. $ID_XDMA) ?? "دانەنراوە";
    $MAX = $bot->get('XDMA_INF_MAX__'. $ID_XDMA) ?? "دانەنراوە";
    $PRICE = $bot->get('XDMA_INF_PRICE__'. $ID_XDMA) ?? "دانەنراوە";
    $ID = $bot->get('XDMA_INF_ID__'. $ID_XDMA) ?? "دانەنراوە";
    $description  = $bot->get('XDMA_INF_DESCRIPTION__'. $ID_XDMA) ?? "دانەنراوە";
        $my_text = "

*✅ - دۆمەینی سایت : *[$DOMIN]
*✅ - تۆکنی سایت :* [$API]
*✅ - ئایدی خزمەتگوزاری :* `$ID`
*✅ - زۆرترین بڕ بۆ داواکاری :* `$MAX`
*✅ - کەمترین بڕ بۆ داواکاری :* `$MIN`
*✅ - نرخ بۆ هەر 1 :* *$PRICE*
*✅ - وەسفی خزمەتگوزاری :* [$description]

";
    $NO3_TSLEM = $bot->get('XDMA_INF_TSLEM__'. $ID_XDMA) ?? "ئۆتۆماتیکی";
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*- خزمەتگوزاری $name_xdma کۆنترۆڵ لە خوارەوە 🔠*
$my_text",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "دۆخی خزمەتگوزاری : $status_now", "callback_data" => "toggle_service_$ENTERXDMA_"]],
                [["text" => "جۆری تەسلیمکردن : $NO3_TSLEM", "callback_data" => "TSLEMER_$ENTERXDMA_"]],
                [["text" => "دیاریکردنی ناوی خزمەتگوزاری", "callback_data" => "setinfosX_$ENTERXDMA_|_|_|NAME"]],
                [["text" => "دیاریکردنی ئایدی خزمەتگوزاری", "callback_data" => "setinfosX_$ENTERXDMA_|_|_|ID"]],
                [["text" => "دیاریکردنی کەمترین بڕ", "callback_data" => "setinfosX_$ENTERXDMA_|_|_|MIN"]],
                [["text" => "دیاریکردنی زۆرترین بڕ", "callback_data" => "setinfosX_$ENTERXDMA_|_|_|MAX"]],
                [["text" => "دیاریکردنی نرخ", "callback_data" => "setinfosX_$ENTERXDMA_|_|_|PRICE"]],
                [["text" => "دیاریکردنی وەسف", "callback_data" => "setinfosX_$ENTERXDMA_|_|_|DESCRIPTION"]],
                [["text" => "دیاریکردنی دۆمەینی سایت", "callback_data" => "setinfosX_$ENTERXDMA_|_|_|DOMIN"]],
                [["text" => "دیاریکردنی کلیل [API_KEY]", "callback_data" => "setinfosX_$ENTERXDMA_|_|_|KEY"]],
                [["text" => "$YOU_CAN", "callback_data" => "autox_$ENTERXDMA_"]],
                [["text" => "سڕینەوەی خزمەتگوزاری", "callback_data" => "deletexdma_$ENTERXDMA_"]],
                [["text" => "🔙 گەڕانەوە", "callback_data" => "ENTERQSM_$in"]]
            ]
        ])
    ]);
    $sessions->delete('mode_'.$from_id);
    $sessions->delete('help_'.$from_id);
}

$setinfosX_ = explode("setinfosX_", $data)[1];
if ($setinfosX_) {
    $DATA = explode("|_|_|", $setinfosX_);
    $ID_XDMA = $DATA[0];
    $action = $DATA[1];
    if ($action == "NAME") {$ACTK = "ناوی خزمەتگوزاری";}
    if ($action == "ID") {$ACTK = "ئایدی خزمەتگوزاری";}
    if ($action == "MIN") {$ACTK = "کەمترین بڕ";}
    if ($action == "MAX") {$ACTK = "زۆرترین بڕ";}
    if ($action == "DOMIN") {$ACTK = "دۆمەینی سایت";}
    if ($action == "KEY") {$ACTK = "کلیلی [API_KEY]";}
    if ($action == "PRICE") {$ACTK = "نرخی خزمەتگوزاری";}
    if ($action == "DESCRIPTION") {$ACTK = "وەسفی خزمەتگوزاری";}
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*‌ئێستا $ACTK بنێرە:*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "ENTERXDMA_$ID_XDMA"]]
            ]
        ])
    ]);
    $sessions->set("mode_$from_id", "EDITXDMAX");
    $sessions->set("help_$from_id", $action);
    $sessions->set("help2_$from_id", $ID_XDMA);
}

if($text and $sessions->get("mode_". $chat_id) == "EDITXDMAX"){
    $action = $sessions->get('help_' . $from_id);
    $ID_XDMA = $sessions->get('help2_' . $from_id);

    if($action == "ID"){$ACTK = "ئایدی خزمەتگوزاری";}
    if($action == "MIN"){$ACTK = "کەمترین بڕ";}
    if($action == "MAX"){$ACTK = "زۆرترین بڕ";}
    if($action == "DOMIN"){$ACTK = "دۆمەینی سایت";
    $IMBERO = parse_url($text);
    $text = $IMBERO['host'] ?? $text;}
    if($action == "KEY"){$ACTK = "کلیلی [API_KEY]";}
    if($action == "PRICE"){$ACTK = "نرخی خزمەتگوزاری";}
    if($action == "DESCRIPTION"){$ACTK = "وەسفی خزمەتگوزاری";}
    
    $OLD = $bot->get('XDMA_INF_'.$action .'__'. $ID_XDMA) ?? "NONE";
    $BEST_TEXT = "*- کۆن :* $OLD\n*- نوێ :* $text";

    if($action == "NAME"){
        $ACTK = "ناوی خزمەتگوزاری";
        $OLD_NAME = $bot->get("xdmatname_".$ID_XDMA);
        $QSM_ID = $bot->get("xdmatinqsm_".$ID_XDMA);

        if ($OLD_NAME && $QSM_ID) {
            $bot->set("xdmatname_".$ID_XDMA, $text);
            $services_list = $bot->get('xdmat_' . $QSM_ID);
            $new_services_list = str_replace($OLD_NAME, $text, $services_list);
            $bot->set('xdmat_' . $QSM_ID, $new_services_list);
            $bot->delete('xdmat_' . $OLD_NAME);
            $bot->set('xdmat_' . $text, $ID_XDMA);

            $BEST_TEXT = "*- کۆن :* $OLD_NAME\n*- نوێ :* $text";
        }
    } else {
        $bot->set('XDMA_INF_'.$action .'__'. $ID_XDMA, $text);
    }

    bot('SendMessage', [
        'chat_id' => $chat_id, 
        'text' => "*($ACTK) بە سەرکەوتوویی پاشەکەوت کرا ✅.*\n\n$BEST_TEXT",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "ENTERXDMA_$ID_XDMA"]]
            ]
        ])
    ]);
    
    $sessions->delete('mode_' . $from_id);
    $sessions->delete('help_' . $from_id);
    $sessions->delete('help2_' . $from_id);
}


$autox_ = explode("autox_", $data)[1];
if($autox_){
    $name_xdma = $bot->get('xdmatname_' . $autox_) ?? '0';
    $DOMIN = $bot->get('GENERALS_DOMIN');
    $API = $bot->get('GENERALS_KEY');
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*خزمەتگوزاری $name_xdma ڕێکخرا بۆ ئەوەی ببەسترێتەوە بە $DOMIN ✅*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "ENTERXDMA_$autox_"]]
            ]
        ])
    ]);
    $bot->set('XDMA_INF_DOMIN__'. $autox_, $DOMIN);
    $bot->set('XDMA_INF_KEY__'. $autox_, $API);
}

if (preg_match("/^شێوازی_پیشاندانی_(.*)/", $data, $m)) {
    $ENTERQSM = $m[1];
    $current_style = $bot->get('style_qsm_' . $ENTERQSM);
    $new_style = ($current_style == 'ستوونی') ? 'ئاسۆیی' : 'ستوونی';
    $bot->set('style_qsm_' . $ENTERQSM, $new_style);

    $name_qsm = $bot->get('qsms_name_' . $ENTERQSM);
    $S_LIST = ['inline_keyboard' => []];
    $buttons = [];

    foreach (explode("\n", $bot->get('xdmat_' . $ENTERQSM)) as $xdmats) {
        $idx = $bot->get('xdmat_' . $xdmats);
        if (!empty($xdmats) and !empty($idx)) {
            $buttons[] = ['text' => "$xdmats", 'callback_data' => "ENTERXDMA_$idx"];
        }
    }

    if ($new_style == 'ستوونی') {
        foreach ($buttons as $btn) {
            $S_LIST['inline_keyboard'][] = [$btn];
        }
    } else {
        $button_rows = array_chunk($buttons, 2);
        foreach ($button_rows as $row) {
            $S_LIST['inline_keyboard'][] = $row;
        }
    }

    // هێنانی دۆخی بەشەکە
    $status_now = $bot->get('qsm_status_' . $ENTERQSM) ?? '✅';

    $S_LIST['inline_keyboard'][] = [["text" => "شێوازی پیشاندان : " . $new_style, "callback_data" => "شێوازی_پیشاندانی_$ENTERQSM"]];
    $S_LIST['inline_keyboard'][] = [["text" => "سیستەمی 24 کاتژمێر : " . $bot->get('toggle_24_' . $ENTERQSM), "callback_data" => "toggles_24_$ENTERQSM"]];
    $S_LIST['inline_keyboard'][] = [["text" => "دۆخی بەش : " . $status_now, "callback_data" => "toggle_qsm_status_$ENTERQSM"]];
    $S_LIST['inline_keyboard'][] = [["text" => "زیادکردنی خزمەتگوزاری ➕", "callback_data" => "addxdmat_$ENTERQSM"]];
    $S_LIST['inline_keyboard'][] = [["text" => "سڕینەوەی بەش 🗑️", "callback_data" => "confirm_delete_qsm_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "گۆڕینی ناوی بەش ✏️", "callback_data" => "ask_new_name_for_$ENTERQSM"]];
    $S_LIST['inline_keyboard'][] = [["text" => "‌ناردنی ناوی خزمەتگوزارییەکان 📇", "callback_data" => "names_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "هێنانی نوسخەی یەدەگ 📥", "callback_data" => "BACKUPX_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "بەرزکردنەوەی نوسخەی یەدەگ 📤", "callback_data" => "UPLOAD_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "🔙 گەڕانەوە", "callback_data" => "xdmats"]];

    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- بەشی $name_qsm کۆنترۆڵ لە خوارەوە 🔠*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode($S_LIST)
    ]);
}

$ENTERQSM_ = explode('ENTERQSM_', $data)[1] ?? null;

if ($ENTERQSM_) {
    if(!$bot->get('style_qsm_' .$ENTERQSM_)){
        $bot->set('style_qsm_' .$ENTERQSM_ , 'ستوونی');
    }
    if(!$bot->get('toggle_24_'.$ENTERQSM_)){
        $bot->set('toggle_24_'.$ENTERQSM_,'❌');
    }
    
    $name_qsm = $bot->get('qsms_name_' . $ENTERQSM_);
    
    $S_LIST = ['inline_keyboard' => []];
    $buttons = [];

    foreach (explode("\n", $bot->get('xdmat_' . $ENTERQSM_)) as $xdmats) {
        $idx = $bot->get('xdmat_' . $xdmats);
        if (!empty($xdmats) and !empty($idx)) {
            $buttons[] = ['text' => "$xdmats", 'callback_data' => "ENTERXDMA_$idx"];
        }
    }

    if ($bot->get('style_qsm_' .$ENTERQSM_) == 'ستوونی') {
        foreach ($buttons as $btn) {
            $S_LIST['inline_keyboard'][] = [$btn];
        }
    } else {
        $button_rows = array_chunk($buttons, 2);
        foreach ($button_rows as $row) {
            $S_LIST['inline_keyboard'][] = $row;
        }
    }
    
    $sessions->delete('mode_' . $from_id);
    $sessions->delete('help_' . $from_id);
    
    $status_now = $bot->get('qsm_status_' . $ENTERQSM_) ?? '✅';

    $S_LIST['inline_keyboard'][] = [["text" => "شێوازی پیشاندان : " . $bot->get('style_qsm_' .$ENTERQSM_), "callback_data" => "شێوازی_پیشاندانی_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "سیستەمی 24 کاتژمێر : ". $bot->get('toggle_24_'.$ENTERQSM_), "callback_data" => "toggles_24_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "دۆخی بەش : " . $status_now, "callback_data" => "toggle_qsm_status_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "زیادکردنی خزمەتگوزاری ➕", "callback_data" => "addxdmat_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "سڕینەوەی بەش 🗑️", "callback_data" => "confirm_delete_qsm_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "گۆڕینی ناوی بەش ✏️", "callback_data" => "ask_new_name_for_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "‌ناردنی ناوی خزمەتگوزارییەکان 📇", "callback_data" => "names_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "هێنانی نوسخەی یەدەگ 📥", "callback_data" => "BACKUPX_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "بەرزکردنەوەی نوسخەی یەدەگ 📤", "callback_data" => "UPLOAD_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "🔙 گەڕانەوە", "callback_data" => "xdmats"]];

    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- بەشی $name_qsm کۆنترۆڵ لە خوارەوە 🔠*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode($S_LIST)
    ]);
}
$ALLASGENERAL_ = explode("ALLASGENERAL_" , $data)[1];
if($ALLASGENERAL_){
    
    $xdmat_list = $bot->get('xdmat_' . $ALLASGENERAL_);
    if ($xdmat_list) {
        foreach (explode("\n", $xdmat_list) as $xdmats) {
            $xdmats = trim($xdmats);
            if (!empty($xdmats)) {
                $idx = $bot->get('xdmat_' . $xdmats);
                if (!empty($idx)) {
                    $bot->set('GENERALS_DOMINX_'. $idx , 'OK');
                }
            }
        }
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'text' => "*- هەموی بەسترایەوە *",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "🔙 گەڕانەوە", "callback_data" => "ENTERQSM_$ALLASGENERAL_"]],
                ]
            ])
        ]);
    }
}
$UPLOAD_ = explode("UPLOAD_", $data)[1];

if ($UPLOAD_) {
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- باشە، فایلی نوسخەی یەدەگ بنێرە بە فۆرماتی (BOT)*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "ENTERQSM_$UPLOAD_"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, "upload"); 
    $sessions->set('help_' . $from_id, $UPLOAD_);
}



if ($sessions->get('mode_' . $from_id) === 'upload' && isset($update->message->document)) {
    $file_id = $update->message->document->file_id;
    $file_info = bot("getFile", ["file_id" => $file_id]);
    $file_path = $file_info->result->file_path ?? null;

    if ($file_path) {
        if (pathinfo($file_path, PATHINFO_EXTENSION) === "BOT") {
            $download_url = "https://api.telegram.org/file/bot" . API_KEY . "/" . $file_path;
            $content = @file_get_contents($download_url);

            if ($content !== false) {
                $lines = explode("\n", trim($content));
                $added_names = '';
                $qsm_id = $sessions->get('help_' . $from_id);
                $added_count = 0;
                $skipped_count = 0;

                foreach ($lines as $line) {
                    $line = trim($line);

                    if (empty($line)) continue;
                    if (strpos($line, '(+)-') === 0) {

                        $clean_line = substr($line, 4);
                        
                        $fields = explode('|', $clean_line);
                        
                        list($NAME, $idx, $DOMIN, $API, $ID, $MAX, $MIN, $PRICE, $description) = array_pad($fields, 9, null);

                        if (empty(trim($NAME)) || empty(trim($idx))) {
                            $skipped_count++;
                            continue;
                        }
                        $bot->set('xdmat_' . $NAME, $idx);
                        $bot->set('xdmatname_' . $idx, $NAME);
                        $bot->set('xdmatinqsm_' . $idx, $qsm_id);
                        
                        $bot->set('XDMA_INF_DOMIN__' . $idx, trim($DOMIN));
                        $bot->set('XDMA_INF_KEY__' . $idx, trim($API));
                        $bot->set('XDMA_INF_ID__' . $idx, trim($ID));
                        $bot->set('XDMA_INF_MAX__' . $idx, trim($MAX));
                        $bot->set('XDMA_INF_MIN__' . $idx, trim($MIN));
                        $bot->set('XDMA_INF_PRICE__' . $idx, trim($PRICE));
                        $bot->set('XDMA_INF_DESCRIPTION__' . $idx, trim($description));
                        
                        $old_xdmat_list = $bot->get('xdmat_' . $qsm_id) ?? '';
                        $updated_list = trim($old_xdmat_list . "\n" . $NAME);
                        $bot->set('xdmat_' . $qsm_id, $updated_list);

                        $added_names .= "➤ `$NAME`\n";
                        $added_count++;
                    }
                }
                $sessions->delete('mode_' . $from_id);
                $sessions->delete('help_' . $from_id);
                
                $final_message = "*✅ فایلەکە بە سەرکەوتوویی جێبەجێ کرا.*\n\n";
                $final_message .= "*خزمەتگوزارییە زیادکراوەکان ($added_count):*\n$added_names";
                if ($skipped_count > 0) {
                    $final_message .= "\n\n*⚠️ ژمارەی $skipped_count خزمەتگوزاری تێپەڕێنران بەهۆی کەمی داتا.*";
                }

                bot('sendMessage', [
                    'chat_id' => $chat_id,
                    'text' => $final_message,
                    'parse_mode' => 'Markdown'
                ]);

            } else {
                bot('sendMessage', ['chat_id' => $chat_id, 'text' => "❌ شکستی هێنا لە دابەزاندنی ناوەڕۆکی فایل. دووبارە هەوڵ بدەرەوە."]);
            }
        } else {
            bot('sendMessage', ['chat_id' => $chat_id, 'text' => "❌ ئەو فایلەی ناردووتە بە فۆرماتی (.bero) ی دروست نییە!"]);
        }
    } else {
        bot('sendMessage', ['chat_id' => $chat_id, 'text' => "❌ شکستی هێنا لە وەرگرتنی زانیاری فایل لە تێلیگرام."]);
    }
}


$BACKUPX_ = explode("BACKUPX_", $data)[1];
if ($BACKUPX_) {
    $name_qsm = $bot->get('qsms_name_' . $BACKUPX_);
    $sessions->delete('mode_' . $from_id);
    $sessions->delete('help_' . $from_id);

    $allData = '';
    $xdmat_list = $bot->get('xdmat_' . $BACKUPX_);
    if ($xdmat_list) {
        foreach (explode("\n", $xdmat_list) as $xdmats) {
            $xdmats = trim($xdmats);
            if (!empty($xdmats)) {
                $idx = $bot->get('xdmat_' . $xdmats);
                if (!empty($idx)) {

                    $DOMIN = $bot->get('XDMA_INF_DOMIN__' . $idx) ?? 'N/A';
                    $API = $bot->get('XDMA_INF_KEY__' . $idx) ?? 'N/A';
                    $ID = $bot->get('XDMA_INF_ID__' . $idx) ?? 'N/A';
                    $MAX = $bot->get('XDMA_INF_MAX__' . $idx) ?? 'N/A';
                    $MIN = $bot->get('XDMA_INF_MIN__' . $idx) ?? 'N/A';
                    $PRICE = $bot->get('XDMA_INF_PRICE__' . $idx) ?? 'N/A';
                    $description = $bot->get('XDMA_INF_DESCRIPTION__' . $idx) ?? 'N/A';

                    $info_line = "$DOMIN|$API|$ID|$MAX|$MIN|$PRICE|$description";
                    
                    $allData .= "(+)-$xdmats|$idx|$info_line\n";
                }
            }
        }
    }

    $filename = "backup_$BACKUPX_.BOT";
    file_put_contents($filename, $allData);

    bot('sendDocument', [
        'chat_id' => $chat_id,
        'document' => new CURLFile(realpath($filename)),
        'caption' => "✅ نوسخەی یەدەگی تەواو بۆ بەشی: $name_qsm پاشەکەوت کرا",
    ]);

    unlink($filename);
}


$ENTERQSM_x = explode('toggles_24_',$data)[1];
if($ENTERQSM_x){
    $ENTERQSM_ = $ENTERQSM_x;
    if($bot->get('toggle_24_'.$ENTERQSM_) != '✅'){
        $bot->set('toggle_24_'.$ENTERQSM_  , '✅'); 
    }else{
        $bot->set('toggle_24_'.$ENTERQSM_  , '❌'); 
    }
    $name_qsm = $bot->get('qsms_name_' . $ENTERQSM_);
    $sessions->delete('mode_' . $from_id);
    $sessions->delete('help_' . $from_id);

    $S_LIST = ['inline_keyboard' => []];
    $buttons = [];

    foreach (explode("\n", $bot->get('xdmat_' . $ENTERQSM_)) as $xdmats) {
        $idx = $bot->get('xdmat_' . $xdmats);
        if (!empty($xdmats) and !empty($idx)) {
            
            $buttons[] = ['text' => "$xdmats", 'callback_data' => "ENTERXDMA_$idx"];
        }
    }

    if ($bot->get('style_qsm_' . $ENTERQSM_) == 'ئاسۆیی') {
        $button_rows = array_chunk($buttons, 2);
        foreach ($button_rows as $row) {
            $S_LIST['inline_keyboard'][] = $row;
        }
    } else {
        foreach ($buttons as $btn) {
            $S_LIST['inline_keyboard'][] = [$btn];
        }
    }

    $status_now = $bot->get('qsm_status_' . $ENTERQSM_) ?? '✅';

    $S_LIST['inline_keyboard'][] = [["text" => "شێوازی پیشاندان : " . $bot->get('style_qsm_' .$ENTERQSM_), "callback_data" => "شێوازی_پیشاندانی_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "سیستەمی 24 کاتژمێر : ". $bot->get('toggle_24_'.$ENTERQSM_), "callback_data" => "toggles_24_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "دۆخی بەش : " . $status_now, "callback_data" => "toggle_qsm_status_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "زیادکردنی خزمەتگوزاری ➕", "callback_data" => "addxdmat_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "سڕینەوەی بەش 🗑️", "callback_data" => "confirm_delete_qsm_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "گۆڕینی ناوی بەش ✏️", "callback_data" => "ask_new_name_for_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "‌ناردنی ناوی خزمەتگوزارییەکان 📇", "callback_data" => "names_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "هێنانی نوسخەی یەدەگ 📥", "callback_data" => "BACKUPX_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "بەرزکردنەوەی نوسخەی یەدەگ 📤", "callback_data" => "UPLOAD_$ENTERQSM_"]];
    $S_LIST['inline_keyboard'][] = [["text" => "🔙 گەڕانەوە", "callback_data" => "xdmats"]];

    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- بەشی $name_qsm کۆنترۆڵ لە خوارەوە 🔠*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode($S_LIST)
    ]);
}

$setinfos_ = explode("setinfos_", $data)[1] ?? null;
if ($setinfos_) {
    
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*- باشە زانیارییەکان بەم شێوەیە بنێرە 📝*\n
[SITE_DOMAIN|API_KEY|ID_SERVICE|MAX|MIN|PRICE_COIN|DESCRIPTION]\n*نموونە*\n`example.com|8457rjfher484|3346|1000|100|0.08|بەستەر بنێرە`",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "ENTERXDMA_$setinfos_"]],
            ]
        ])
    ]);
    $sessions->set('mode_' . $from_id, 'editxdma');
    $sessions->set('help_' . $from_id, $setinfos_);
}

if ($sessions->get('mode_' . $from_id) === 'editxdma' && !empty($text)) {
    $ID_XDm = $sessions->get('help_' . $from_id);
    $qsm_id = $wallets->get('xdmatinqsm_' . $sessions->get('help_' . $from_id));
    $S_TEXT = explode('|', $text);
    
    if (count($S_TEXT) >= 6) {
        [$DOMIN, $API, $ID, $MAX, $MIN, $PRICE , $description] = $S_TEXT;
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*- زانیاری خزمەتگوزاری پاشەکەوت کرا ✅*\n- دۆمەینی سایت : `$DOMIN`\n- تۆکنی سایت : `$API`\n- ئایدی خزمەتگوزاری : `$ID`\n- زۆرترین بڕ بۆ داواکاری : `$MAX`\n- کەمترین بڕ بۆ داواکاری : `$MIN`\n- نرخ بۆ هەر 1 : *$PRICE* 
وەسفی خزمەتگوزاری : [$description]",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "🔙 گەڕانەوە", "callback_data" => "ENTERXDMA_$ID_XDm"]]
                ]
            ])
        ]);
        $bot->set('infos_' . $sessions->get('help_' . $from_id), $text);
        $sessions->delete('mode_' . $from_id);
        $sessions->delete('help_' . $from_id);
    } else {
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*- هەڵە دڵنیابەرەوە لە شێوازی داواکراو ❌*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "🔙 گەڕانەوە", "callback_data" => "ENTERXDMA_" . $sessions->get('help_' . $from_id)]]
                ]
            ])
        ]);
    }
}

$addxdmat_ = explode("addxdmat_",$data)[1];
if($addxdmat_){
    $name_qsm = $bot->get('qsms_name_'.$addxdmat_);
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
       'text' => "*- ناوی خزمەتگوزاری بنێرە بۆ زیادکردنی بۆ بەشی $name_qsm ✅*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "ENTERQSM_$addxdmat_"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id,'addxdma');
    $sessions->set('help_'.$from_id,$addxdmat_);
    return;
}

if($sessions->get('mode_'.$from_id) == 'addxdma' && $text){
    $idx = coderandom(10);
    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => "*- خزمەتگوزاری $text کۆنترۆڵ لە خوارەوە 🔠*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode( [
            'inline_keyboard' => [
                [["text" => "دیاریکردنی زانیاری", "callback_data" => "ENTERXDMA_$idx"]],
                [["text" => "🔙 گەڕانەوە", "callback_data" => "xdmats"]]
            ]
        ])
    ]);
    $bot->set('xdmat_'.$text,$idx);
    $bot->set('xdmatname_'.$idx,$text);
    $bot->set('xdmatinqsm_'.$idx,$sessions->get('help_'.$from_id));
    $bot->set('xdmat_'. $sessions->get('help_'.$from_id) ,$bot->get('xdmat_'. $sessions->get('help_'.$from_id))."\n$text");
    $sessions->delete('mode_'.$from_id);
    $sessions->delete('help_'.$from_id);
}

if (strpos($data, "ACCEDK_") === 0) {
    $parts = explode('_', str_replace('ACCEDK_', '', $data));
    $m_id = $parts[0] ?? null;
    $c_id = $parts[1] ?? null;

    if ($m_id && $c_id) {
        bot('editMessageReplyMarkup', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "ئاگاداری بۆ ئەندام نێردرا ", "url" => "tg://user?id=$c_id"]],
                ]
            ])
        ]);

        bot('sendMessage', [
            'chat_id' => $c_id,
            'text' => "*- داواکارییەکەت تەواو بوو ✅*",
            'parse_mode' => 'Markdown',
            'reply_to_message_id' => $m_id,
        ]);
    }
}

if($data == 'addqsm'){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
       'text' => "*- ناوێک بنێرە بۆ بەشەکە ✅*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "xdmats"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id,'addqsm');
    return;
}

if($sessions->get('mode_'.$from_id) == 'addqsm' && $text){
    $idx = coderandom(10);
    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => "*- بەشی $text کۆنترۆڵ لە خوارەوە 🔠*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "زیادکردنی خزمەتگوزاری ➕", "callback_data" => "addxdmat_$idx"]],
                [["text" => "🔙 گەڕانەوە", "callback_data" => "xdmats"]]
            ]
        ])
    ]);
    $sessions->delete('mode_'.$from_id);
    $sessions->delete('help_'.$from_id);
    $bot->set('qsms',$bot->get('qsms')."\n$text");
    $bot->set('qsms_id_'.$text,$idx);
    $bot->set('qsms_name_'.$idx,$text);
    $bot->set('qsm_status_' . $idx, '✅');
}

if($data == 'makelinkhdia' or $data === 'make_hdia'){
    $type_text = ($data == 'makelinkhdia') ? "بەستەر 🔗" : "کۆد 🎫";
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
       'text' => "*• دروستکردنی $type_text بۆ دیاری 🎁*

- تکایە بڕی $a3ml لەناو دیارییەکە بنێرە (بۆ هەر کەسێک):",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACKADMIN"]],
            ]
        ])
    ]);
    $sessions->set('type_'.$from_id, $data);
    $sessions->set('mode_'.$from_id, 'makelinkhdia');
}

if($sessions->get('mode_'.$from_id) == 'makelinkhdia' && is_numeric($text)){
    if($sessions->get('type_'.$from_id) == 'makelinkhdia'){
        $type = 'بەستەرەکە';
    } else {
        $type = 'کۆدەکە';
    }
    
    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => "*- چەند بەکارهێنەر دەتوانێت سوود لە $type وەربگرێت؟ 👥*\n\n(ژمارەی ئەو کەسانە بنێرە کە دەتوانن دیارییەکە وەربگرن)",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACKADMIN"]]
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id, 'makelinkhdia2');
    $sessions->set('help_'.$from_id, $text);
    return;
}

if($sessions->get('mode_'.$from_id) == 'makelinkhdia2' && is_numeric($text)){
    $amount = $sessions->get('help_'.$from_id);
    $count_users = $text;

    if($sessions->get('type_'.$from_id) == 'makelinkhdia'){
        $get = coderandom(32);
        
        $sessions->set('hdia_'.$get, $amount);
        $sessions->set('hdia_count_'.$get, $count_users);
        $sessions->set('hdia_count_now_'.$get, 0);

        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "✅ *بەستەری دیاری بە سەرکەوتوویی دروستکرا*

💰 *بڕ:* $amount $a3ml
👥 *ژمارەی کەس:* $count_users
🔗 *بەستەر:* 
`https://t.me/$USRBOT?start=hdia$get`

- دەتوانیت بەستەرەکە کۆپی بکەیت و بڵاوی بکەیتەوە.",
            'parse_mode' => 'Markdown',
        ]);

        $sessions->delete('mode_'.$from_id);
        $sessions->delete('help_'.$from_id);
        $sessions->delete('help2_'.$from_id);
    } 
    else {
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*🔤 ئێستا ئەو وشەیە (کۆدە) بنێرە کە دەتەوێت بیکەیت بە دیاری*\n\nنموونە: `RAMADAN` یان `GIFT2024`",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "🔙 گەڕانەوە", "callback_data" => "BACKADMIN"]]
                ]
            ])
        ]);
        $sessions->set('mode_'.$from_id, 'makelinkhdia3');
        $sessions->set('help2_'.$from_id, $count_users); // Count
    }
    return;
}

if($sessions->get('mode_'.$from_id) == 'makelinkhdia3'){
    $amount = $sessions->get('help_'.$from_id);
    $count_users = $sessions->get('help2_'.$from_id);
    $code_text = $text;

    if($sessions->get('hdia_'.$code_text)){
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "⚠️ *ئەم کۆدە پێشتر بەکارهاتووە!* تکایە ناوێکی تر بنێرە.",
            'parse_mode' => 'Markdown',
        ]);
        return;
    }

    $sessions->set('hdia_'.$code_text, $amount);
    $sessions->set('hdia_count_'.$code_text, $count_users);
    $sessions->set('hdia_count_now_'.$code_text, 0);

    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => "✅ *کۆدی دیاری بە سەرکەوتوویی دروستکرا*

💰 *بڕ:* $amount $a3ml
👥 *ژمارەی کەس:* $count_users
🎫 *کۆد:* `$code_text`

- دەتوانیت کۆدەکە کۆپی بکەیت و بڵاوی بکەیتەوە.",
        'parse_mode' => 'Markdown',
    ]);

    $sessions->delete('mode_'.$from_id);
    $sessions->delete('help_'.$from_id);
    $sessions->delete('help2_'.$from_id);
    return;
}

if($data == 'removecoins'){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
       'text' => "*- ئایدی ئەندام بنێرە 🆔:*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "SETTINGER"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id,'remover');
}

if($sessions->get('mode_'.$from_id) == 'remover' && is_numeric($text)){
    $user_id = $text;
    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => "*- ژمارەی $a3ml بنێرە بۆ کەمکردنەوەی لە بەکارهێنەر 🆔:* `$user_id`",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "SETTINGER"]]
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id, 'remove_amount');
    $sessions->set('target_user', $user_id);
} 
elseif ($sessions->get('mode_'.$from_id) == 'remove_amount' && is_numeric($text)) {
    $amount_to_remove = intval($text);
    $target_user = $sessions->get('target_user');

    if($amount_to_remove > 0){
        $current_points = $wallets->get('coins_'.$target_user) ?? 0;
        $new_balance = max(0, $current_points - $amount_to_remove);
        $actually_deducted = $current_points - $new_balance;

        $wallets->set('coins_'.$target_user, $new_balance);

        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*✅ بڕی* `$actually_deducted` *$a3ml لە بەکارهێنەر کەمکرایەوە* 🆔 `$target_user`\n*باڵانسی نوێ:* `$new_balance`",
            'parse_mode' => 'Markdown'
        ]);
        
        bot('SendMessage', [
            'chat_id' => $target_user,
            'text' => "*- ئاگاداری: بڕی* `$actually_deducted` *$a3ml لە باڵانسەکەت کەمکرایەوە لەلایەن بەڕێوەبەرایەتی.*",
            'parse_mode' => 'Markdown'
        ]);
        $sessions->delete('mode_'.$from_id);
        $sessions->delete('target_user');

    } else {
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*❌ تکایە ژمارەیەکی دروست بنێرە!*",
            'parse_mode' => 'Markdown'
        ]);
    }
}


if($data == 'addcoins'){    
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
       'text' => "*- ئایدی ئەندام بنێرە 🆔:*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "SETTINGER"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id,'adder');
}

if($sessions->get('mode_'.$from_id) == 'adder' && is_numeric($text)){
    $user_id = $text;
    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => "*- ژمارەی $a3ml بنێرە بۆ زیادکردنی بۆ بەکارهێنەر 🆔:* `$user_id`",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "SETTINGER"]]
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id, 'add_amount');
    $sessions->set('target_user', $user_id);
} 
elseif ($sessions->get('mode_'.$from_id) == 'add_amount' && is_numeric($text)) {
    $amount = intval($text);
    $target_user = $sessions->get('target_user');

    if($amount > 0){
        $current_points = $wallets->get('coins_'.$target_user) ?? 0;
        $wallets->set('coins_'.$target_user, $current_points + $amount);

        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*✅ بڕی* `$amount` *$a3ml بۆ بەکارهێنەر زیادکرا* 🆔 `$target_user`",
            'parse_mode' => 'Markdown'
        ]);

        bot('SendMessage', [
            'chat_id' => $target_user, 
            'text' => "*- ئاگاداری: بڕی* `$amount` *$a3ml بۆ باڵانسەکەت زیادکرا لەلایەن بەڕێوەبەرایەتی.*",
            'parse_mode' => 'Markdown'
        ]);
        
        $sessions->delete('mode_'.$from_id);
        $sessions->delete('target_user');
    } else {
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*❌ تکایە ژمارەیەکی دروست و ئەرێنی بنێرە!*",
            'parse_mode' => 'Markdown'
        ]);
    }
}

if($data == "alqnwat"){
    bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "لێرە دەتوانیت کەناڵ و هەژمار دابنێیت 😇",
        'show_alert' => true,
    ]);
    $data = 'alta3en';
}
if($data == "alnsos"){
    bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "لێرە دەتوانیت دەق و کڵێشە دابنێیت 😩",
        'show_alert' => true,
    ]);
    $data = 'alta3en';
}
if($data == "alnqat"){
    bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "لێرە دەتوانیت ڕێکخستنەکانی $a3ml دابنێیت 👊",
        'show_alert' => true,
    ]);
    $data = 'alta3en';
}
if($data=='SET_TH_NSHR'){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
      'text' => "*- پەیامی داواکاری ئێستا بنێرە :*
 (⌯ ئەو هاشتاگانەی ڕێگەت پێدراوە بەکاریان بهێنیت.)
 - `#a` - *بۆ دانانی ناوی بەکارهێنەر و تێیدا بەستەری هەژمار*
 - `#b` - *بۆ دانانی ناوی هەژمار*
 - `#c` - *بۆ دانانی ئایدی هەژمار*
 - `#d` - *بۆ دانانی یوزەری بەکارهێنەر*
 - `#e` - *بۆ دانانی ژمارەی $a3ml*
 - `#f` - *بۆ دانانی ناوی خزمەتگوزاری*
 - `#g` - *بۆ دانانی ئایدی داواکاری*
 - `#h` - *بۆ دانانی ژمارەی داواکارییەکان*
 - `#i` - *بۆ دانانی نرخی داواکاری*
 - `#j` - *بۆ دانانی ژمارەی داواکراو*
 - `#k` - *بۆ دانانی ناوی بەش*",
        'parse_mode' => 'Markdown', 
       'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "rsala_nshr"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id , $data);
    return;
}
if($text and $sessions->get('mode_'.$from_id) == "SET_TH_NSHR"){
    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => "*- پەیامی بڵاوکردنەوە پاشەکەوت کرا .*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                
                [["text" => "گەڕانەوە", "callback_data" => "rsala_nshr"]]
            ]
        ])
    ]);
    
    $TH_START = str_replace(array('#a','#b' , '#c' , '#d' , '#e') , array("[$name](tg://user?id=$from_id)" ,"$name" , "$from_id" , "[$username]" ,$wallets->get('coins_'.$chat_id)) , $text);
    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => "*- نموونەیەک بۆ پەیامی بڵاوکردنەوە.*
$TH_START",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                
                [["text" => "گەڕانەوە", "callback_data" => "rsala_nshr"]]
            ]
        ])
    ]);

    $bot->set('rsala_nshr_text', "$text");
    $sessions->delete('mode_'.$from_id);
}
if($data == 'rsala_nshr'){

    $NOW_STA =  $bot->get('rsala_nshr_text');
bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
      'text' => "*- بەشی پەیامی بڵاوکردنەوەی داواکاری  .*
 ⌯ ئێستا: `$NOW_STA`",
        'parse_mode' => 'Markdown', 
       'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "دیاریکردنی پەیام", "callback_data" => "SET_TH_NSHR"]],
                [["text" => "گەڕانەوە", "callback_data" => "alta3en"]],
            ]
        ])
    ]);

}

if($data == 'alta3en'){
    $amla_text = $bot->get('amla_text') ?? 'خاڵ';
    $shares_coin = $bot->get('share') ?? "200";
    $hdia = $bot->get('hdia') ?? "75";
    $a3mola = $bot->get('3mola') ?? "15";
    $MEMBER_COIN = $bot->get("membertmoil") ?? "10";
    $JOINER_COIN = $bot->get("JOINtmoil") ?? "5";
    $name_text = $bot->get('name_bot') ?? "Your Support";

    $tmoil_min = $bot->get('tmoil_min') ?? "10";
    $tmoil_max = $bot->get('tmoil_max') ?? "5000";

    $channel_bot = $bot->get('chs_bot') ?? "@SSFSBOTS";
    $channel_tlbat = $bot->get('chs_tlbat') ?? "نییە";
    $channel_support = $bot->get('chs_support') ?? "هەژماری خاوەن";

    $rsala_nshr_text = $bot->get('rsala_nshr_text') ?? 'بنەڕەتی';
    $siana_status = $bot->get('siana') ? 'دەق' : 'بنەڕەتی';
    $policy_status = $bot->get('policy') ? 'دەق' : 'نییە';
    $payed_status = $bot->get('payed') ? 'دەق' : 'نییە';
    $expl_status = $bot->get('explanation_text') ? 'دەق' : 'نییە';
    $link_status = $bot->get('linkurl') ? 'بەستەر' : 'نییە';

    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*- بەشی دەستکاریکردنەکان، دەتوانیت لێرە کۆنترۆڵیان بکەیت ✅*
",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "تایەی بەخت", "callback_data" => "LUCK_SECTION"],["text" => "ڕێکخستن", "callback_data" => "LUCK_SECTION"]],
                [["text" => "دیاری هەفتانە", "callback_data" => "ALHDIA_SBo3"],["text" => "ڕێکخستن", "callback_data" => "ALHDIA_SBo3"]],
                
                [["text" => "- کەناڵەکان + هەژمار -", "callback_data" => "alqnwat"]],
                [["text" => "پشتیوانی تەکنیکی", "callback_data" => "setch_support"],["text" => "$channel_support", "callback_data" => "setch_support"]],
                [["text" => "کەناڵی بۆت", "callback_data" => "setch_bot"],["text" => "$channel_bot", "callback_data" => "setch_bot"]],
                [["text" => "کەناڵی داواکارییەکان", "callback_data" => "setch_tlbat"],["text" => "$channel_tlbat", "callback_data" => "setch_tlbat"]],
                [["text" => "پەیامی بڵاوکردنەوەی داواکاری", "callback_data" => "rsala_nshr"],["text" => "$rsala_nshr_text", "callback_data" => "rsala_nshr"]],
                
                [["text" => "- دەقەکان -", "callback_data" => "alnsos"]],
                [["text" => "ناوی دراوی بۆت", "callback_data" => "setct_amla_text"],["text" => "$amla_text", "callback_data" => "setct_amla_text"]],
                [["text" => "ناوی بۆت", "callback_data" => "setct_name_bot"],["text" => "$name_text", "callback_data" => "setct_name_bot"]],
                [["text" => "پەیامی چاکسازی", "callback_data" => "setct_siana"],["text" => "$siana_status", "callback_data" => "setct_siana"]],
                [["text" => "پەیامی $a3ml کڕین", "callback_data" => "setct_payed"],["text" => "$payed_status", "callback_data" => "setct_payed"]],
                [["text" => "مەرج و ڕێساکان", "callback_data" => "setct_policy"],["text" => "$policy_status", "callback_data" => "setct_policy"]],
                
                [["text" => "دەقی ڕوونکردنەوە", "callback_data" => "setct_explanation_text"],["text" => "$expl_status", "callback_data" => "setct_explanation_text"]],
                [["text" => "بەستەری ڕوونکردنەوە", "callback_data" => "setct_linkurl"],["text" => "$link_status", "callback_data" => "setct_linkurl"]],
                
                [["text" => "- $a3ml -", "callback_data" => "alnqat"]],
                [["text" => "کەمترین ژمارەی ئەندام", "callback_data" => "set_tmoil_min"],["text" => "$tmoil_min", "callback_data" => "set_tmoil_min"]],
                [["text" => "زۆرترین ژمارەی ئەندام", "callback_data" => "set_tmoil_max"],["text" => "$tmoil_max", "callback_data" => "set_tmoil_max"]],
                [["text" => "جۆینی کەناڵەکان ئەندام", "callback_data" => "setcc_JOINtmoil"],["text" => "$JOINER_COIN", "callback_data" => "setcc_JOINtmoil"]],
                [["text" => "نرخ یەک ئەندام", "callback_data" => "setcc_membertmoil"],["text" => "$MEMBER_COIN", "callback_data" => "setcc_membertmoil"]],
                [["text" => "بڵاوکردنەوەی بەستەر", "callback_data" => "setcc_share"],["text" => "$shares_coin", "callback_data" => "setcc_share"]],
                [["text" => "دیاری", "callback_data" => "setcc_hdia"],["text" => "$hdia", "callback_data" => "setcc_hdia"]],
                [["text" => "عمولەی گواستنەوە", "callback_data" => "setcc_3mola"],["text" => "$a3mola", "callback_data" => "setcc_3mola"]],
                [["text" => "گەڕانەوە", "callback_data" => "BACKADMIN"]],
            ]
        ])
    ]);
    $sessions->delete('mode_'.$from_id);
    $sessions->delete('help_'.$from_id);
}

if($data == 'set_tmoil_min'){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*• کەمترین ژمارەی ئەندام بنێرە بۆ داواکاری :*
",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "alta3en"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id,'set_tmoil_min_val');
}

if($text and $sessions->get('mode_'.$from_id) == 'set_tmoil_min_val'){
    if(is_numeric($text)){
        $bot->set('tmoil_min', $text);
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "• دیاریکرا $text ✅",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "alta3en"]],
            ]
        ])
        ]);
        $sessions->delete('mode_'.$from_id);
    }else{
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*• لەم بەشە تەنها ناردنی ژمارە ڕێگەپێدراوە ❌*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "alta3en"]],
            ]
        ])
        ]);
    }
}


if($data == 'set_tmoil_max'){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*• زۆرترین ژمارەی ئەندام بنێرە بۆ داواکاری :*
",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "alta3en"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id,'set_tmoil_max_val');
}

if($text and $sessions->get('mode_'.$from_id) == 'set_tmoil_max_val'){
    if(is_numeric($text)){
        $bot->set('tmoil_max', $text);
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "• دیاریکرا $text ✅",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "alta3en"]],
            ]
        ])
        ]);
        $sessions->delete('mode_'.$from_id);
    }else{
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*• لەم بەشە تەنها ناردنی ژمارە ڕێگەپێدراوە ❌*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "alta3en"]],
            ]
        ])
        ]);
    }
}

if(!$bot->get('ALhdia_3bo3iaa')){
$bot->set('ALhdia_3bo3iaa' , '❌');
}

$bbLuck = explode('bbLuck_' , $data)[1];
if($bbLuck){
    $RR = $bot->get('Luck_enabled');
    $TO = ($RR == '✅') ? '❌' : '✅';
    $bot->set('Luck_enabled', $TO);
    $data = 'LUCK_SECTION';
}


if($data == 'LUCK_SECTION'){
    $from = $bot->get('Luck_from') ?? "10";
    $to = $bot->get('Luck_to') ?? "100";
    $status = $bot->get('Luck_enabled') ?? '❌';

    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*- بەشی تایەی بەخت 🎯*
- خاڵەکان لە: $from بۆ: $to
- دۆخ: $status
",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "دۆخ : $status", "callback_data" => "bbLuck_1"]],
                [["text" => "دیاریکردنی کەمترین و زۆرترین", "callback_data" => "setLuckRange"]],
                [["text" => "گەڕانەوە", "callback_data" => "alta3en"]],
            ]
        ])
    ]);
    $sessions->delete('mode_'.$from_id);
    return;
}


if($data == 'setLuckRange'){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "• کەمترین و زۆرترین بنێرە بەم شێوەیە:\n`10-100`\n(تەنها ژمارە و - لە نێوانیان)",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [['text'=>'گەڕانەوە','callback_data'=>'LUCK_SECTION']]
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id, 'set_LUCK_RANGE');
    return;
}

if($sessions->get('mode_'.$from_id) == 'set_LUCK_RANGE'){
    if(preg_match('/^(\d+)-(\d+)$/', $text, $match)){
        $min = (int)$match[1];
        $max = (int)$match[2];

        if($min < $max){
            $bot->set('Luck_from', $min);
            $bot->set('Luck_to', $max);
            bot('SendMessage', [
                'chat_id' => $chat_id,
                'text' => "✅ تایەی بەخت دیاریکرا لە *$min* بۆ *$max* $a3ml.",
                'parse_mode' => 'Markdown',
                'reply_markup' => json_encode([
                    'inline_keyboard' => [
                        [['text'=>'گەڕانەوە','callback_data'=>'LUCK_SECTION']]
                    ]
                ])
            ]);
            $sessions->delete('mode_'.$from_id);
        }else{
            bot('SendMessage', [
                'chat_id' => $chat_id,
                'text' => "⚠️ دەبێت کەمترین بچووکتر بێت لە زۆرترین. دووبارە هەوڵ بدەرەوە:",
            ]);
        }
    }else{
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "⚠️ شێوازەکە هەڵەیە. بەکاری بهێنە وەک: `10-100`",
            'parse_mode' => 'Markdown'
        ]);
    }
    return;
}

$bbHdia_ = explode('bbHdia_' , $data)[1];
if($bbHdia_){
    $RR= $bot->get('ALhdia_3bo3iaa');
    if($RR=='✅'){
        $TO = '❌';
    }else{
        $TO = '✅';
    }
    $bot->set('ALhdia_3bo3iaa' , $TO);
    $data = 'ALHDIA_SBo3';
}
if($data == 'ALHDIA_SBo3'){
    $a3d_hdia=$bot->get('ALhdia_3bo3ia') ?? '100';
    $hala_a3bo3 = $bot->get('ALhdia_3bo3iaa');
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*- بەشی دیاری هەفتانە ✅*
- ژمارەی دیاری : $a3d_hdia
",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "دۆخ : $hala_a3bo3", "callback_data" => "bbHdia_3bo3"]],
                [["text" => "دیاریکردنی ژمارە", "callback_data" => "t3en_ALHDIA_SBo3"]],
             
                [["text" => "گەڕانەوە", "callback_data" => "alta3en"]],
            ]
        ])
    ]);
    $sessions->delete('mode_'.$from_id);
    $sessions->delete('help_'.$from_id);
}

if($data == 't3en_ALHDIA_SBo3'){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "• ژمارەی دیارییە هەفتانەکان بنێرە (تەنها ژمارە):",
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [['text'=>'گەڕانەوە','callback_data'=>'ALHDIA_SBo3']]
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id, 'set_ALHDIA_SBo3');
    return;
}

if($sessions->get('mode_'.$from_id) == 'set_ALHDIA_SBo3'){
    if(is_numeric($text)){
        $bot->set('ALhdia_3bo3ia', $text);
        bot('SendMessage', [
        'chat_id' => $chat_id,
            'text' => "✅ ژمارەی دیارییە هەفتانەکان دیاریکرا بە: *$text*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [['text'=>'گەڕانەوە','callback_data'=>'ALHDIA_SBo3']]
                ]
            ])
        ]);
        $sessions->delete('mode_'.$from_id);
    }else{
        bot('SendMessage', [
        'chat_id' => $chat_id,
            'text' => "⚠️ تکایە تەنها ژمارە بنووسە، دووبارە هەوڵ بدەرەوە:",
        ]);
    }
    return;
}

$setch_ = explode("setch_" , $data)[1];
if($setch_){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*• یوزەر بنێرە (تەنها یوزەر) 😺*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "alta3en"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id,'seter2');
    $sessions->set('help_'.$from_id,$setch_);
}

if($text and $sessions->get('mode_'.$from_id) == 'seter2'){
    $user = str_replace('@', '' , $text);
    $bot->set('chs_' . $sessions->get('help_'.$from_id) , $user);
    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => "*• پاشەکەوت کرا *([@$user]) ✅",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
        'inline_keyboard' => [
            [["text" => "گەڕانەوە", "callback_data" => "alta3en"]],
        ]
    ])
    ]);
    $sessions->delete('mode_'.$from_id);
$sessions->delete('help_'.$from_id);
}
$setcc_ = explode("setct_",$data)[1];
if($setcc_){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*• ناوەڕۆک بنێرە بۆ پاشەکەوتکردن :*
",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "alta3en"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id,'seter1');
    $sessions->set('help_'.$from_id,$setcc_);
}
if($text and $sessions->get('mode_'.$from_id) == 'seter1'){
        $bot->set($sessions->get('help_'.$from_id),$text);
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "• ناوەڕۆک دیاریکرا ✅",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "alta3en"]],
            ]
        ])
        ]);
        $sessions->delete('mode_'.$from_id);
    $sessions->delete('help_'.$from_id);
    
}


$setcc_ = explode("setcc_",$data)[1];
if($setcc_){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*• ژمارە بنێرە بۆ پاشەکەوتکردن :*
",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "alta3en"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id,'seter');
    $sessions->set('help_'.$from_id,$setcc_);
}
if($text and $sessions->get('mode_'.$from_id) == 'seter'){
    if(is_numeric($text)){
        $bot->set($sessions->get('help_'.$from_id),$text);
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "• دیاریکرا $text ✅",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "alta3en"]],
            ]
        ])
        ]);
        $sessions->delete('mode_'.$from_id);
    $sessions->delete('help_'.$from_id);
    }else{
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*• لەم بەشە تەنها ناردنی ژمارە ڕێگەپێدراوە ❌*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "alta3en"]],
            ]
        ])
        ]);
    }
    
}

$STARTBLOCK_ = explode('STARTBLOCK_' , $data)[1];
if($STARTBLOCK_){
    $BLOCKSx = $bot->get("blocks") ?? [];
    if (!in_array($STARTBLOCK_, $BLOCKSx)) {
        $BLOCKSx[] = $STARTBLOCK_;
        $bot->set("blocks", $BLOCKSx);
        bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "بەکارهێنەر $STARTBLOCK_ بلۆک کرا ✅",
        'show_alert' => true,
    ]);
    }else{
        bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "ئەم بەکارهێنەرە $STARTBLOCK_ پێشتر بلۆک کراوە ⚠️",
        'show_alert' => true,
    ]);
    }
}

}else{


$ref_code = null;
if (strpos($text, "/start ") === 0) {
    $parts = explode(' ', $text);
    if (isset($parts[1]) && !empty($parts[1])) {
        $ref_code = $parts[1];
        $cache->set('pending_referral_' . $from_id, $ref_code);
    }
}

if (isset($from_id) && isset($chat_type) && $chat_type == 'private' && !$users->get($from_id)) {
    if ($name != null) {
        $users->set($from_id, $name);
        
        $entry_method = "یوزەری بۆت";
        if ($ref_code) {
            if (preg_match('/by/', $ref_code)) {
                $entry_method = "بەستەری گواستنەوە";
            } elseif (preg_match('/hdia/', $ref_code)) {
                $entry_method = "بەستەری دیاری";
            } else {
                $entry_method = "بەستەری بانگهێشت";
            }
        }

        if ($bot->get('generals_entry') != '❌') {
            $mems = count($users->getAllWithPrefix('')); 
            $user_link = "[$name](tg://user?id=$from_id)";
            $username_txt = $username ? "[@$username]" : "نییە";

            foreach ($ADMINS as $admin_id) {
                bot('SendMessage', [
                    'chat_id' => $admin_id,
                    'text' => "*👤 ئەندامێکی نوێ هاتە ناو بۆت*\n\n" .
                              "*• ناو :* $user_link \n" .
                              "*• ئایدی :* `$from_id`\n" .
                              "*• یوزەر :* $username_txt\n" .
                              "*• هاتە ژوورەوە لە ڕێگەی :* $entry_method\n\n" .
                              "*• کۆی گشتی ئەندامان : $mems 🔗*",
                    'parse_mode' => 'Markdown',
                ]);
            }
        }
    }
}

if ($bot->get('HIMAIA_passworder') == 'چالاک ✅' && $bot->get('HRMZAR_RMZ')) {
    if(!$security->get("I_UER_$from_id")){
        if (strpos($text, "/start") === 0) {
            bot('SendMessage', [
                'chat_id' => $chat_id,
                'text' => "*• بەکارهێنانت ڕەتکرایەوە بەهۆی پاراستنی تایبەت ❌*\n- تکایە کۆدی نهێنی بنووسە بۆ چوونەژوورەوە :",
                'parse_mode' => 'Markdown',
            ]);
            $sessions->set('mode_' . $from_id, 'IM_IN_HMAIAA_PASSWORD');
            return;
        }

        if ($text && $sessions->get('mode_' . $from_id) == 'IM_IN_HMAIAA_PASSWORD') {
            if ($text == $bot->get('HRMZAR_RMZ')) {
                $security->set("3DD_MSMOH_" , $security->get("3DD_MSMOH_") + 1);
                $NOW_CC = $security->get("3DD_MSMOH_");
                
                $ALLOWS = $security->get("ALLOWS") ?? [];
                if (!in_array($from_id, $ALLOWS)) {
                    $ALLOWS[] = $from_id;
                    $security->set("ALLOWS", $ALLOWS);
                }
                $ALMSMOHEN = count($ALLOWS);

                bot('SendMessage', [
                    'chat_id' => $chat_id,
                    'text' => "*• کۆدی نهێنی دروستە، دەتوانێت بۆت بەکاربهێنیت ✅*\n- تکایە بنێرە /start .",
                    'parse_mode' => 'Markdown',
                ]);

                if($bot->get('HIMAIA_notifa') == "✅"){
                    bot('SendMessage', [
                        'chat_id' => $ADMIN,
                        'text' => "*🔔 ئاگاداری: تێپەڕاندنی پاراستن*

👤 *زانیاری بەکارهێنەر:*
*• ناو:* [$name](tg://user?id=$from_id)
*• یوزەر:* [@$user]
*• ئایدی:* $from_id

🔐 *ڕێگەی چوونەژوورەوە:*
*• جۆر: کۆدی نهێنی*
*• کۆدی بەکارهێنراو:* $text

*- ژمارەی ڕێگەپێدراوان: $ALMSMOHEN*",
                        'parse_mode' => 'Markdown',
                        'reply_markup' => json_encode([
                            'inline_keyboard' => [
                                [["text" => "🚫 بلۆککردنی بەکارهێنەر", "callback_data" => "STARTBLOCK_$from_id"]],
                            ]
                        ])
                    ]);
                }
                
                $sessions->delete('mode_' . $from_id);
                $security->set("I_UER_$from_id" , 'ok');
            } else {
                bot('SendMessage', [
                    'chat_id' => $chat_id,
                    'text' => "*• کۆدی چوونەژوورەوە هەڵەیە ❌*\n- تکایە دڵنیابەرەوە لە کۆدەکە و دووبارە هەوڵ بدەرەوە.",
                    'parse_mode' => 'Markdown',
                ]);
            }
            return;
        }
    }
}

if($bot->get('HIMAIA_LIN_KER') == 'چالاک ✅' and $security->get('THE_LINK')){
    if(!$security->get("I_UER_$from_id")){
    if(preg_match('/start/' , $text)){
        $U = explode("start " , $text)[1] ?? '';
        
        if($U == $security->get('THE_LINK')){
            $security->set("3DD_MSMOH_" , $security->get("3DD_MSMOH_") + 1);
            $NOW_CC = $security->get("3DD_MSMOH_");
            
            $ALLOWS = $security->get("ALLOWS") ?? [];
            if (!in_array($from_id, $ALLOWS)) {
                $ALLOWS[] = $from_id;
                $security->set("ALLOWS", $ALLOWS);
            }
            $ALMSMOHEN = count($ALLOWS);

            bot('SendMessage', [
                    'chat_id' => $chat_id,
                    'text' => "*• بەستەری چوونەژوورەوە دروستە، دەتوانێت بۆت بەکاربهێنیت ✅*\n- تکایە بنێرە /start .",
                    'parse_mode' => 'Markdown',
                ]);
                
                if($bot->get('HIMAIA_notifa') == "✅"){
                    bot('SendMessage', [
                        'chat_id' => $ADMIN,
                        'text' => "*🔔 ئاگاداری: تێپەڕاندنی پاراستن*

👤 *زانیاری بەکارهێنەر:*
*• ناو:* [$name](tg://user?id=$from_id)
*• یوزەر:* [@$user]
*• ئایدی:* $from_id

🔐 *ڕێگەی چوونەژوورەوە:*
*• جۆر: بەستەری چوونەژوورەوە*
*• بەستەر:* [Link](https://t.me/$usrbot?start=$THE_LINK)

*- ژمارەی ڕێگەپێدراوان: $ALMSMOHEN*",
                        'parse_mode' => 'Markdown',
                        'reply_markup' => json_encode([
                            'inline_keyboard' => [
                                [["text" => "🚫 بلۆککردنی بەکارهێنەر", "callback_data" => "STARTBLOCK_$from_id"]],
                            ]
                        ])
                    ]);
                }
                
                $security->set("I_UER_$from_id" , 'ok');
                return;
        } 
    }
    bot('SendMessage', [
                'chat_id' => $chat_id,
                'text' => "*• بەکارهێنانت ڕەتکرایەوە بەهۆی پاراستنی تایبەت ❌*",
                'parse_mode' => 'Markdown',
            ]);
            
    return;
        }
}

if (preg_match("/^EMOJI_VERIF_(.*)$/", $data, $match)) {
    $user_choice = $match[1];
    $expected = $sessions->get("HELPER_$from_id");

    if ($expected == $user_choice) {
        $security->set("I_UER3_$from_id", 'ok'); 
        $security->set("3DD_MSMOH_" , $security->get("3DD_MSMOH_") + 1);
        $NOW_CC = $security->get("3DD_MSMOH_");
        
        $ALLOWS = $security->get("ALLOWS") ?? [];
        if (!in_array($from_id, $ALLOWS)) {
            $ALLOWS[] = $from_id;
            $security->set("ALLOWS", $ALLOWS);
        }
        $ALMSMOHEN = count($ALLOWS);
        
        bot('editMessageText', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'text' => "*• پشکنینی ئیمۆجی سەرکەوتوو بوو ✅*\n- تکایە بنێرە /start .",
            'parse_mode' => 'Markdown',
        ]);

        $sessions->delete("HELPER_$from_id");
        $sessions->delete("mode_" . $from_id); 

        if ($bot->get('HIMAIA_notifa') == "✅") {
            bot('SendMessage', [
                'chat_id' => $ADMIN,
                'text' => "*🔔 ئاگاداری: تێپەڕاندنی پاراستن*

👤 *زانیاری بەکارهێنەر:*
*• ناو:* [$name](tg://user?id=$from_id)
*• یوزەر:* [@$user]
*• ئایدی:* $from_id

🔐 *ڕێگەی چوونەژوورەوە:*
*• جۆر: پشکنینی ئیمۆجی 🐾*

*- ژمارەی ڕێگەپێدراوان: $ALMSMOHEN*",
                'parse_mode' => 'Markdown',
                'reply_markup' => json_encode([
                    'inline_keyboard' => [
                        [["text" => "🚫 بلۆککردنی بەکارهێنەر", "callback_data" => "STARTBLOCK_$from_id"]]
                    ]
                ])
            ]);
        }
    } else {
        bot('answerCallbackQuery', [
            'callback_query_id' => $update->callback_query->id,
            'text' => "❌ هەڵبژاردن هەڵەیە! دووبارە هەوڵ بدەرەوە.",
            'show_alert' => true
        ]);
    }
}

if ($bot->get('HIMAIA_EMOJI_CHECK') == "✅") {
    if (!$security->get("I_UER3_$from_id")) {
        
        if (strpos($text, '/start') === 0) {
            $captcha = sendEmojiCaptcha($chat_id);
            $sessions->set("HELPER_" . $from_id, $captcha['code']);
            $sessions->set('mode_' . $from_id, 'EMOJI_CAPTCHA_PENDING'); 
            return;
        }

        $is_in_captcha_mode = ($sessions->get('mode_' . $from_id) == 'EMOJI_CAPTCHA_PENDING');
        if ($is_in_captcha_mode) {
            if (isset($update->callback_query)) {
            } else {
                return;
            }
        }
    }
}

if ($bot->get('HIMAIA_THQQ_BSRY') == "✅") {
    if (!$security->get("I_UER2_$from_id")) {    
        if (strpos($text, "/start") === 0) {
            $T = sendCaptcha($chat_id);
            $sessions->set('HELPER_' . $from_id, $T['code']);
            $sessions->set('mode_' . $from_id, 'IM_IN_HIMAIA_THQQ_BSRY');
            return;
        }

        if ($sessions->get('mode_' . $from_id) == 'IM_IN_HIMAIA_THQQ_BSRY') {
            $expected_code = $sessions->get('HELPER_' . $from_id);
            if ($text == $expected_code) {
                $security->set("3DD_MSMOH_" , $security->get("3DD_MSMOH_") + 1);
                $NOW_CC = $security->get("3DD_MSMOH_");
                
                $ALLOWS = $security->get("ALLOWS") ?? [];
                if (!in_array($from_id, $ALLOWS)) {
                    $ALLOWS[] = $from_id;
                    $security->set("ALLOWS", $ALLOWS);
                }
                $ALMSMOHEN = count($ALLOWS);
                
                bot('SendMessage', [
                    'chat_id' => $chat_id,
                    'text' => "*• پشکنینی بینایی سەرکەوتوو بوو ✅*\n- تکایە بنێرە /start .",
                    'parse_mode' => 'Markdown',
                ]);

                if ($bot->get('HIMAIA_notifa') == "✅") {
                    bot('SendMessage', [
                        'chat_id' => $ADMIN,
                        'text' => "*🔔 ئاگاداری: تێپەڕاندنی پاراستن*

👤 *زانیاری بەکارهێنەر:*
*• ناو:* [$name](tg://user?id=$from_id)
*• یوزەر:* [@$user]
*• ئایدی:* $from_id

🔐 *ڕێگەی چوونەژوورەوە:*
*• جۆر: پشکنینی بینایی*

*- ژمارەی ڕێگەپێدراوان: $ALMSMOHEN*",
                        'parse_mode' => 'Markdown',
                        'reply_markup' => json_encode([
                            'inline_keyboard' => [
                                [["text" => "🚫 بلۆککردنی بەکارهێنەر", "callback_data" => "STARTBLOCK_$from_id"]],
                            ]
                        ])
                    ]);
                }
                $sessions->delete('HELPER_' . $from_id);
                $sessions->delete('mode_' . $from_id);

                $security->set("I_UER2_$from_id", 'ok');
                return;
            }
        }
        return;
    }
}

if ($bot->get('HIMAIA_JIHAT_ITSAL') == '✅') {
    if (!$sessions->get('JIHAT_ITSAL_' . $from_id)) {
        if (strpos($text, '/start') === 0) {
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => "تکایە ژمارەی مۆبایلەکەت (Contact) بنێرە بۆ پشتڕاستکردنەوە",
                'reply_to_message_id' => $message_id,
                'reply_markup' => json_encode([
                    'keyboard' => [
                        [['text' => '📱 ناردنی ژمارەی مۆبایل', 'request_contact' => true]]
                    ],
                    'resize_keyboard' => true,
                    'one_time_keyboard' => true
                ])
            ]);
            $sessions->set('mode_' . $from_id, 'IM_IN_HIMAIA_JIHAT_ITSAL');
            return;
        }

        if (isset($update->message->contact->phone_number)) {
            $PHONE = $update->message->contact->phone_number;
            if ($update->message->contact->user_id == $from_id) {
                
                $ALLOWS = $security->get("ALLOWS") ?? [];
                if (!in_array($from_id, $ALLOWS)) {
                    $ALLOWS[] = $from_id;
                    $security->set("ALLOWS", $ALLOWS);
                }
                $ALMSMOHEN = count($ALLOWS);

                bot('SendMessage', [
                    'chat_id' => $chat_id,
                    'text' => "*• پشکنینی ژمارە سەرکەوتوو بوو ✅*\n- تکایە بنێرە /start .",
                    'parse_mode' => 'Markdown',
                ]);

                if ($bot->get('HIMAIA_notifa') == "✅") {
                    bot('SendMessage', [
                        'chat_id' => $ADMIN,
                        'text' => "*🔔 ئاگاداری: تێپەڕاندنی پاراستن*

👤 *زانیاری بەکارهێنەر:*
*• ناو:* [$name](tg://user?id=$from_id)
*• یوزەر:* [@$user]
*• ئایدی:* $from_id

🔐 *ڕێگەی چوونەژوورەوە:*
*• جۆر: ژمارەی مۆبایل*

*- ژمارەی ڕێگەپێدراوان: $ALMSMOHEN*",
                        'parse_mode' => 'Markdown',
                        'reply_markup' => json_encode([
                            'inline_keyboard' => [
                                [["text" => "🚫 بلۆککردنی بەکارهێنەر", "callback_data" => "STARTBLOCK_$from_id"]],
                            ]
                        ])
                    ]);
                }

                $sessions->set('JIHAT_ITSAL_' . $from_id, 'ok');
            } else {
                bot('SendMessage', [
                    'chat_id' => $chat_id,
                    'text' => "*• ژمارەی مۆبایلەکە ساختەیە و هی ئەم هەژمارە نییە ❌*",
                    'parse_mode' => 'Markdown',
                ]);
            }
            return;
        }
    }
}


    $F = explode('start ', $text)[1] ?? null;

    if (!$F) {
        $pending_ref = $cache->get('pending_referral_' . $from_id);
        if ($pending_ref) {
            $F = $pending_ref;
        }
    }

    if ($F) {
        $mode = $F;
        $دخل = "بەستەری بانگهێشت";
        if (preg_match('/by/', $F)) {
            $دخل = "بەستەری گواستنەوە";
        }
        if (preg_match('/hdia/', $F)) {
            $دخل = "بەستەری دیاری";
        }

    } else {
        $mode = 'BACK';
        $دخل = "یوزەری بۆت";
    }
    
$channels = $forced_join->get('channels') ?: [];

if (!empty($channels)) {
    $x = 0;
    $keyboard = [];
    $need_save = false;

    foreach ($channels as $index => $channel) {
        $required_count = $forced_join->get("channel_count_$index") ?: 0;
        $current_count = $join_tracker->get("channel_count_$index") ?: 0;

        if ($required_count != 'x' && $required_count > 0 && $current_count >= $required_count) {
            bot('SendMessage', [
                'chat_id' => $ADMIN,
                'text' => "*ژمارەی داواکراو بۆ جۆینی ناچاری تەواو بوو ✅*\n• کەناڵ : [$channel]\n• ژمارەی گەیشتوو : *$required_count*",
                'parse_mode' => 'Markdown'
            ]);
            
            unset($channels[$index]);
            $need_save = true;
            
            $forced_join->delete("channel_count_$index");
            $join_tracker->delete("channel_count_$index");
            continue; 
        }

        $is_subscribed = X_neW($channel, $chat_id);
        
        $subscription_status = $is_subscribed ? "✅ جۆین کراوە" : "❌ جۆین نەکراوە";

        $keyboard[] = [
            ['text' => "$channel", 'url' => "https://t.me/" . ltrim($channel, '@')],
            ['text' => "$subscription_status", 'url' => "https://t.me/" . ltrim($channel, '@')],
        ];

        if (!$is_subscribed) {
            $x += 1;
            if($join_tracker->get("MODANA_{$from_id}_{$index}") != 'DONE'){
                $join_tracker->set("MODANA_{$from_id}_{$index}", "NO");
            }
        } else {
            if($join_tracker->get("MODANA_{$from_id}_{$index}") != 'DONE'){
                $join_tracker->set("MODANA_{$from_id}_{$index}", "OK");
            }
        }
    }

    if ($need_save) {
        $forced_join->set('channels', array_values($channels));
    }

    if ($x >= 1) {
        $keyboard[] = [['text' => "پشکنینی جۆینی کەناڵەکان ✅", 'callback_data' => "checkchk_$mode"]];
        $reply_markup = json_encode(['inline_keyboard' => $keyboard]);
        $msg = "❗️┇ببورە ئازیزم، دەبێت جۆینی کەناڵەکانی بۆت بکەیت بۆ بەکارهێنان:";

        $ref_code_to_save = explode('start ', $text)[1] ?? null;
        if ($ref_code_to_save) {
            $cache->set('pending_referral_' . $from_id, $ref_code_to_save);
        }

        if (!$data) {
            bot('SendMessage', [
                'chat_id' => $chat_id,
                'text' => $msg,
                'reply_markup' => $reply_markup,
            ]);
        } else {
            bot('EditMessageText', [
                'chat_id' => $chat_id,
                'message_id' => $message_id,
                'text' => $msg,
                'reply_markup' => $reply_markup,
            ]);
        }

        return; 
    }
}

if (isset($channels) && is_array($channels)) {
    foreach ($channels as $ind => $chan) {
        $status = $join_tracker->get("MODANA_{$from_id}_{$ind}");
        if ($status == "OK") {
            $required = $forced_join->get("channel_count_$ind") ?: 0;
            $current = $join_tracker->get("channel_count_$ind") ?: 0;

            if (($current < $required || $required == 'x')) {

                $join_tracker->set("channel_count_$ind", $current + 1);
                $join_tracker->set("MODANA_{$from_id}_{$ind}" , 'DONE');
            }
        }
    }
}

$checkchk_ = explode('checkchk_',$data)[1];
if($checkchk_){
    if($checkchk_ == 'BACK'){
        $data = 'BACK';
    }else{
        bot('DeleteMessage', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
        ]);
        $text = '/start '. $checkchk_;
    }
}

    if($bot->get('generals_siana') == "✅"){
        $siana = $bot->get('siana') ?? "ببورە بۆت لەژێر چاکسازی دایە لە ئێستادا ⚒️";
        if($text){
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "$siana",
            'parse_mode' => 'Markdown',
        ]);
        $text = '';
    }
        if($data){
            bot('answerCallbackQuery',[
                'callback_query_id' => $update->callback_query->id,
                'text' => str_replace('*','',$siana),
                'show_alert' => true,
            ]);
        $data = '';
        }
    }
}
function isBotAdmin($chat_id) {
    $bot_info = bot('getMe');
    if (!isset($bot_info->result->id)) {
        return false;
    }
    
    $bot_id = $bot_info->result->id;
    $admins = bot('getChatAdministrators', ['chat_id' => $chat_id]);
    
    if (!isset($admins->result)) {
        return false;
    }
    
    foreach ($admins->result as $admin) {
        if ($admin->user->id == $bot_id) {
            return true;
        }
    }
    return false;
}

     $YY = ''; 
    $iLL = 0;

    $hl_mfto7 = $bot->get('al3qobat') ?? 'ناچالاک ❌';
    $YU = $bot->get('nqat_xsm') ?? 10;



    if ($hl_mfto7 != 'ناچالاک ❌') {
        $SEENOR = $funding->get("SEEN_$from_id");
      

        foreach ($SEENOR as $RT) {
            if ($funding->get("JOINED_{$RT}_$from_id")) {
                $INFOS = $funding->get('INFOS_' . $RT);
                $parts = explode('|', $INFOS);
                list($COUNT, $PRICE_TMOIL, $CHANNEL, $OWNER) = array_pad($parts, 4, 'N/A');

                if ($CHANNEL != 'N/A' && isBotAdmin($CHANNEL)) {
                    $subscription_status = X_neW($CHANNEL, $from_id) ? "✅ جۆین کراوە" : "❌ جۆین نەکراوە";

                    if ($subscription_status == "❌ جۆین نەکراوە") {
                        $mgh = $funding->get("mghadra_$from_id") ?: [];

                        if (!in_array($RT, $mgh)) {
                            $mgh[] = $RT;
                            $funding->set("mghadra_$from_id", $mgh);

                            $YY .= "[$CHANNEL] | دەرچوو ❌\n";
                            $iLL += 1;
                        }
                    }
                }
            }
        }
    }

    if ($iLL > 0) {
        $ijmale = $YU * $iLL;
        $current_coins = intval($wallets->get('coins_'.$from_id));
        $new_balance = max(0, $current_coins - $ijmale);

        bot('SendMessage', [
            'chat_id' => $from_id,
            'text' => "$YY\n- بڕی *$ijmale* خاڵ کەمکرایەوە لە خاڵەکانت 
*⁉️ بۆچی؟ *
- خاڵت پێدرا لە بەرامبەر جۆینکردنی کەناڵەکان بەڵام تۆ مەرجەکانت شکاند و لێیان دەرچوویت
- ئەگەر دووبارە جۆین بکەیتەوە، دواتر داشکاندنی دوو هێندە جێبەجێ دەکرێت ✅",
            'parse_mode' => 'Markdown'
        ]);

        $wallets->set('coins_'.$from_id, $new_balance);
    }


if(preg_match('/start/',$text)){
    $ID = explode('start ', $text)[1];

    if (!$ID) {
        $pending_ref = $cache->get('pending_referral_' . $from_id);
        if ($pending_ref) {
            $ID = $pending_ref;
            $cache->delete('pending_referral_' . $from_id);
        }
    }

    if($ID){
        if(preg_match('/hdia/',$ID)){
            $get = explode('hdia',$ID)[1];
            
            if(!$sessions->get('hdia_'.$get)){
                bot('SendMessage', [
                    'chat_id' => $chat_id,
                    'text' => "⚠️ ئەم بەستەری دیارییە دۆزرایەوە، ڕەنگە بەسەرچووبێت یان هەڵە بێت.",
                    'parse_mode' => 'Markdown',
                ]);
                return;
            }

            $COOIN = $sessions->get('hdia_'.$get);
            $COUNT_HDIA = $sessions->get('hdia_count_'.$get);
            $NOW_COUNT = $sessions->get('hdia_count_now_'.$get) ?? 0;

            if($cache->get('IM_USE_'.$from_id.'_'.$get)){
                bot('SendMessage', [
                    'chat_id' => $chat_id,
                    'text' => "✅ تۆ پێشتر ئەم دیارییەت وەرگرتووە.",
                    'parse_mode' => 'Markdown',
                ]);
                return;
            }

            if($NOW_COUNT < $COUNT_HDIA){
                $my_rank = $NOW_COUNT + 1;
                $sessions->set('hdia_count_now_'.$get, $my_rank);
                
                $wallets->set('coins_'.$from_id, $wallets->get('coins_'.$from_id) + $COOIN);
                $wallets->set('hdiacoins_'.$from_id, $wallets->get('hdiacoins_'.$from_id) + $COOIN);
                $wallets->set('hdiax_'.$from_id, $wallets->get('hdiax_'.$from_id) + 1);
                
                $cache->set('IM_USE_'.$from_id.'_'.$get, true);

                if($my_rank == 1){
                    $msg_content = "🎉 *پیرۆزە پاڵەوان!* 🥇\n\nتۆ *یەکەم کەس* بوویت ئەم دیارییە وەربگریت! 🚀\nبڕی *$COOIN* $a3ml ت دەستکەوت.";
                } else {
                    $msg_content = "✅ *دیارییەکەت وەرگرت!* 🎁\n\nبڕی *$COOIN* $a3ml ت دەستکەوت.\nتۆ کەسی ژمارە *$my_rank* بوویت لە وەرگرتنی ئەم دیارییە. 👥";
                }

                bot('SendMessage', [
                    'chat_id' => $chat_id,
                    'text' => $msg_content,
                    'parse_mode' => 'Markdown',
                ]);

                foreach($ADMINS as $ADMIN){
                    $TBQA = $COUNT_HDIA - $my_rank;
                    bot('SendMessage', [
                        'chat_id' => $ADMIN,
                        'text' => "*🔔 کەسێک بەستەری دیاری بەکارهێنا 👤*\n\n👤 *ناو:* [$name](tg://user?id=$from_id)\n📇 *ئایدی:* `$from_id`\n💰 *بڕی وەرگیراو:* $COOIN $a3ml\n🔢 *ڕیزبەندی:* کەسی $my_rank\n📉 *ژمارەی ماوە:* $TBQA کەس",
                        'parse_mode' => 'Markdown',
                    ]);
                }

            } else {
                bot('SendMessage', [
                    'chat_id' => $chat_id,
                    'text' => "⚠️ ببورە، ژمارەی دیاری کراو بۆ ئەم بەستەرە تەواو بووە.",
                    'parse_mode' => 'Markdown',
                ]);
            }
            return;
        }
        if(!preg_match('/by/',$ID)){
            $ID = berodecode($ID);
            if(is_numeric($ID) && $ID != $from_id && !$invite_logs->get($from_id)){
                $shares_coin = $bot->get('share') ?? "200";
                $name_freind = $users->get($ID);
                bot('SendMessage', [
                    'chat_id' => $chat_id,
                    'text' => "تۆ جۆینی بەستەری بانگهێشتی هاوڕێکەت $name_freind کرد و بڕی $shares_coin $a3ml ی وەرگرت 🤝",
                    'parse_mode' => 'Markdown',
                ]);
                if (($wallets->get('notify_referral_' . $ID) ?? '✅') == '✅') {
                    bot('SendMessage', [
                        'chat_id' => $ID,
                        'text' => "کەسێکی نوێ لە ڕێگەی بەستەری بانگهێشتەوە هاتە ژوورەوە و تۆ بڕی $shares_coin $a3ml ت وەرگرت ➕
- لەلایەن : [$name](tg://user?id=$from_id) | `$from_id` 👤",
                        'parse_mode' => 'Markdown',
                    ]);
                }
                $referrals = $referral_system->get('top_refs') ?? [];
                $referrals[$ID] = ($referrals[$ID] ?? 0) + 1;
            
                $referral_system->set('top_refs', $referrals);
                $wallets->set('countshare_'.$ID,$wallets->get('countshare_'.$ID) + 1);
                $wallets->set('coinsshare_'.$ID,$wallets->get('coinsshare_'.$ID) + $shares_coin);
                $wallets->set('coins_'.$ID,$wallets->get('coins_'.$ID) + $shares_coin);
                $invite_logs->set($from_id, true);
            }
        }else{
            $get = explode('by',$ID)[1];
            $coin_link = $sessions->get('LINK_'.$get);
            $OWNER = $sessions->get('LINK_OWNER_'.$get);
            if($coin_link){
                bot('SendMessage', [
                    'chat_id' => $chat_id,
                    'text' => "*بڕی $coin_link $a3ml بۆ هەژمارەکەت گوازرایەوە لە ڕێگەی بەستەری گواستنەوە ✅*
- لەلایەن : [$OWNER](tg://user?id=$OWNER) 👤",
                    'parse_mode' => 'Markdown',
                ]);
                bot('SendMessage', [
                    'chat_id' => $OWNER,
                    'text' => "*بەستەری گواستنەوەکەت بەکارهێنرا ✅*
- لەلایەن : [$name](tg://user?id=$from_id) | `$from_id`

- بەستەر : https://t.me/$USRBOT?by$get",
                    'parse_mode' => 'Markdown',
                    'disable_web_page_preview' => true,
                ]);
                $wallets->set('transsucces_'.$from_id,$wallets->get('transsucces_'.$from_id) + $coin_link);
                $wallets->set('coins_'.$from_id,$wallets->get('coins_'.$from_id) + $coin_link);
                $sessions->delete('LINK_'.$get);
                $sessions->delete('LINK_OWNER_'.$get);
            }
        }
    }
    $text = '/start';
}


    

$status = $auto_replies->get("replies_enabled") ?: "on";
if ($status == "on" && isset($text)) {
    $sensitivity = $auto_replies->get("sensitivity") ?: "strict";
    $words = explode(",", $auto_replies->get("reply_words") ?: "");

    foreach ($words as $word) {
        $reply = $auto_replies->get("reply_$word");
        if (!$reply) continue;

        $isMatch = ($sensitivity == "strict" && $text === $word) ||
                   ($sensitivity == "loose" && strpos($text, $word) !== false);

        if ($isMatch) {
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => $reply
            ]);
            break;
        }
    }
}


$viewAzd_ = explode('viewAzd_' , $data)[1];
if($viewAzd_){
    $real_text = retrieve_text($viewAzd_);
    $gg = $bot->get("zrs_info_content_" . $real_text);
    $AL_MHTWA = str_replace(array('#name_user','#name' , '#id' , '#username' ) , array("[$name](tg://user?id=$from_id)" ,"$name" , "$from_id" , "[$username]" ) , $gg);
    $type = $bot->get("zrs_type_" . $real_text);

    if($type == 'ALERT'){
        bot('answerCallbackQuery', [
            'callback_query_id' => $update->callback_query->id,
            'text' => $AL_MHTWA,
            'show_alert' => true
        ]);
    }
    elseif($type == 'SEND'){
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "$AL_MHTWA",
            'parse_mode' => 'Markdown',
             'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "BACK"]],
            ]
        ])
        ]);
    }
    elseif($type == 'CONTACT'){
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'text' => "$AL_MHTWA",
            'parse_mode' => 'Markdown',
             'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "گەڕانەوە", "callback_data" => "BACK"]],
            ]
        ])
        ]);
        $sessions->set('mode_' . $from_id, 'CONTACT_MODE');
        $sessions->set('contact_btn_name_' . $from_id, $real_text);
    }
    else {
        bot('EditMessageText', [
            'parse_mode' => 'Markdown',
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'text' => "$AL_MHTWA",
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "گەڕانەوە", "callback_data" => "BACK"]],
                ]
            ])
        ]);
    }
}

if($text == "/start"){
    $count_services = $bot->get('ORDERS') ?? "0";
    $ALASASE = $bot->get('zrar_alasase');
    $inline_keyboard = [];
    $a3ml = $bot->get("currency") ?: "خاڵ";

    if ($ALASASE == '✅') {
        if(($bot->get('B_STATUS_SERVICES') ?: '✅') != '❌'){
            $inline_keyboard[] = [["text" => "خزمەتگوزارییەکان 🛒", "callback_data" => "SERVICES"]];
        }
        if(($bot->get('B_STATUS_TMOIL_x') ?: '✅') != '❌'){
            $inline_keyboard[] = [["text" => "گەشەپێدانی کەناڵەکەت 📣", "callback_data" => "TMOIL_x"]];
        }
        
        $row_money = [];
        if(($bot->get('B_STATUS_plus_coin') ?: '✅') != '❌') $row_money[] = ["text" => "❇️ کۆکردنەوە", "callback_data" => "plus_coin"];
        if(($bot->get('B_STATUS_transfer_coin') ?: '✅') != '❌') $row_money[] = ["text" => "🔁 گواستنەوەی $a3ml", "callback_data" => "transfer_coin"];
        if(!empty($row_money)) $inline_keyboard[] = $row_money;

        $row_acc = [];
        if(($bot->get('B_STATUS_use_code') ?: '✅') != '❌') $row_acc[] = ["text" => "💳 بەکارهێنانی کۆد", "callback_data" => "use_code"];
        if(($bot->get('B_STATUS_acount_me') ?: '✅') != '❌') $row_acc[] = ["text" => "👤 هەژمار", "callback_data" => "acount_me"];
        if(!empty($row_acc)) $inline_keyboard[] = $row_acc;

        $row_orders = [];
        if(($bot->get('B_STATUS_my_tlbs') ?: '✅') != '❌') $row_orders[] = ["text" => "📨 داواکارییەکانم", "callback_data" => "my_tlbs"];
        if(($bot->get('B_STATUS_info_tlb') ?: '✅') != '❌') $row_orders[] = ["text" => "📬 زانیاری داواکاری", "callback_data" => "info_tlb"];
        if(!empty($row_orders)) $inline_keyboard[] = $row_orders;

        $row_stats = [];
        if(($bot->get('B_STATUS_sh7n') ?: '✅') != '❌') $row_stats[] = ["text" => "💸 کڕینی $a3ml", "callback_data" => "sh7n"];
        if(($bot->get('B_STATUS_stats') ?: '✅') != '❌') $row_stats[] = ["text" => "📊 ئامارەکان", "callback_data" => "stats"];
        if(!empty($row_stats)) $inline_keyboard[] = $row_stats;

        $row_info = [];
        if(($bot->get('B_STATUS_bot_help') ?: '✅') != '❌') $row_info[] = ["text" => "⁉️ ڕوونکردنەوە", "callback_data" => "bot_help"];
        if(($bot->get('B_STATUS_aggrement') ?: '✅') != '❌') $row_info[] = ["text" => "📝 مەرجەکان", "callback_data" => "aggrement"];
        if(!empty($row_info)) $inline_keyboard[] = $row_info;

        if(($bot->get('B_STATUS_count_orders') ?: '✅') != '❌'){
            $inline_keyboard[] = [["text" => "✅ ژمارەی داواکارییەکان : $count_services ✅", "callback_data" => "count_orders"]];
        }
    }

    $lines_text = "";
    for ($i = 1; $i <= 20; $i++) {
        $gg = $bot->get("zrs_IN_LINE_$i");
        if ($gg) {
            $lines_text .= $gg . "[in_$i]\n";
        }
    }

    $lines = explode("\n", $lines_text);

    foreach ($lines as $line) {
        preg_match_all('/\[(.*?)\]/', $line, $matches);
        $row = [];

        foreach ($matches[1] as $btn_text) {
            $tt = store_text($btn_text);
            $GG = $bot->get("zrs_info_$btn_text");
            $THDATA = $bot->get("zrs_info_content_$btn_text");

            if ($GG == '【Link / بەستەر】') {
                $UU = 'url';
            } elseif ($GG == '【Text / ناوەڕۆکی دەقی】') {
                $UU = 'callback_data';
                $THDATA = "viewAzd_" . getencode($btn_text);
            } elseif ($GG == '【Shortcut / دوگمەی کورتکراوە】') {
                $UU = 'callback_data';
                $CODE = explode('BB:', $THDATA)[1];
                $THDATA = base64_decode(base64_decode(base64_decode($CODE)));
            } else {
                continue; 
            }

            $row[] = [
                "text" => "$btn_text",
                "$UU" => "$THDATA",
            ];
        }

        if (!empty($row)) {
            $inline_keyboard[] = $row;
        }
    }
    if(in_array($chat_id, $ADMINS)){
        $inline_keyboard[] = [["text" => "🎛 پانێڵی بەڕێوەبەر", "callback_data" => "GOTO_ADMIN_PANEL"]];
    }

    bot('SendMessage', [
        'chat_id' => $chat_id, 
        'text' => "$START",
        'parse_mode' => 'html',
        'disable_web_page_preview' => true,
        'reply_markup' => json_encode(['inline_keyboard' => $inline_keyboard])
    ]);

    $sessions->delete('mode_'.$from_id);

/*
foreach(explode("\n", $cache->get('ORDERS')) as $ORDER){
    if(empty(trim($ORDER))) continue; 

    $OWNER = $cache->get('ORDER_'.$ORDER);
    $MSG_ID = $cache->get('ORDER_MSG_ID_'.$ORDER);
    $INFOS = $cache->get('ORDER_INFO_'.$ORDER);

    if(!$OWNER || !$INFOS) {
        $cache->set('ORDERS', str_replace($ORDER, '', $cache->get('ORDERS')));
        continue;
    }

    $API = explode("|",$INFOS)[0];
    $DOMIN = explode("|" ,$INFOS)[1];
    $link = explode("|",$INFOS)[2];
    $NAME_XDMA = explode("|",$INFOS)[3];
    $timeLeft = date("Y-m-d H:i:s", explode("|",$INFOS)[4]);
    
    $G = @json_decode(file_get_contents("https://$DOMIN/api/v2?key=$API&action=status&order=$ORDER"))->status;

    if($G == 'Completed'){
        bot('SendMessage', [
            'chat_id' => $OWNER,
            'reply_to_message_id' => $MSG_ID,
            'text' => "*✅ داواکارییەکەت بە سەرکەوتوویی تەواو بوو!*\n*📺 ناوی خزمەتگوزاری*: $NAME_XDMA\n*🔗 بەستەر: *  `$link`\n*⏱️ بەرواری داواکاری:* $timeLeft\n*🎉 سوپاس بۆ بەکارهێنانت*",
            'parse_mode' => 'Markdown',
        ]);
        $cache->delete('ORDER_'.$ORDER);
        $cache->delete('ORDER_MSG_ID_'.$ORDER);
        $cache->delete('ORDER_PRICE_'.$ORDER);
        $cache->delete('ORDER_INFO_'.$ORDER);
        $cache->set('ORDERS', str_replace($ORDER, '', $cache->get('ORDERS')));
    }

    if($G == 'Canceled'){
        $irja3 = (int) $cache->get('ORDER_PRICE_'.$ORDER);

        if ($irja3 > 0) {
            bot('SendMessage', [
                'chat_id' => $OWNER,
                'reply_to_message_id' => $MSG_ID,
                'text' => "*داواکاری هەڵوەشایەوە ❌*\n- بڕی *$irja3* $a3ml گەڕێندرایەوە بۆ هەژمارەکەت",
                'parse_mode' => 'Markdown',
            ]);
            $wallets->set('coins_'.$OWNER, $wallets->get('coins_'.$OWNER) + $irja3);
        }
        $cache->delete('ORDER_'.$ORDER);
        $cache->delete('ORDER_PRICE_'.$ORDER);
        $cache->delete('ORDER_MSG_ID_'.$ORDER);
        $cache->delete('ORDER_INFO_'.$ORDER);
        $cache->set('ORDERS', str_replace($ORDER, '', $cache->get('ORDERS')));
    }
}
*/
}

if($data == "bot_help"){
    $text = $bot->get('explanation_text') ?? "هیچ ڕوونکردنەوەیەک لە ئێستادا بەردەست نییە.";
    $link = $bot->get('linkurl');

    $keyboard = [];
    if($link && $link != 'نییە'){
        if(strpos($link, 'http') === 0){
             $keyboard[] = [["text" => "🔗 کرتە بکە بۆ بینین", "url" => $link]];
        }
    }
    $keyboard[] = [["text" => "🔙 گەڕانەوە", "callback_data" => "BACK"]];

    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => $text,
        'parse_mode' => 'Markdown',
        'disable_web_page_preview' => true,
        'reply_markup' => json_encode([
            'inline_keyboard' => $keyboard
        ])
    ]);
}

$a3ml_الاشتراك = $bot->get("JOINtmoil") ?? "5";
$سعر_تمويل = $bot->get("membertmoil") ?? "10";
function GET_RANDOM_CH($from_id) {
    global $funding;

    $ids_raw = $funding->get("IDXS");
    if (!$ids_raw) return false;

    $ids = explode("\n", trim($ids_raw));
    shuffle($ids);

    $checked_channels = [];

    foreach ($ids as $id) {
        $seen = $funding->get("SEEN_$from_id") ?: [];
            if (!in_array($id, $seen)) {
        $INFOS = $funding->get('INFOS_' . $id);
        if (!$INFOS) continue;

        $parts = explode('|', $INFOS);
        list($COUNT, $PRICE_TMOIL, $CHANNEL, $OWNER) = array_pad($parts, 4, 'N/A');

        if (in_array($CHANNEL, $checked_channels)) continue;
        $checked_channels[] = $CHANNEL;

        $member = TMOIL(API_KEY, 'getChatMember', [
            'chat_id' => $CHANNEL,
            'user_id' => $from_id
        ]);

        $data = json_decode(json_encode($member), true);
        if(CHECKIFADMIN($CHANNEL , API_KEY)){
        if (!$data['ok'] || in_array($data['result']['status'], ['left', 'kicked'])) {
            return $CHANNEL . "|" . $id;
        }
    }
    }
    }

    return false;
}

if (preg_match('/^CHKJOIN_(.*)/', $data, $match)) {
    $ID = $match[1];
    $INFOS = $funding->get("INFOS_$ID");
    if ($INFOS) {
        if ($funding->get("JOINED_{$ID}_$from_id")) {
            bot('answerCallbackQuery', [
                'callback_query_id' => $update->callback_query->id,
                'text' => "⚠️ تۆ پێشتر خاڵت بۆ ئەم کەناڵە وەرگرتووە",
                'show_alert' => true
            ]);
            $data = "JOIN_CHANNNELS";
        } else {
            list($COUNT, $PRICE_TMOIL, $CHANNEL, $OWNER) = explode('|', $INFOS);
            $member = TMOIL(API_KEY, 'getChatMember', [
                'chat_id' => $CHANNEL,
                'user_id' => $from_id
            ]);
            $dataM = json_decode(json_encode($member), true);

            if ($dataM['ok'] && !in_array($dataM['result']['status'], ['left', 'kicked'])) {
                $funding->set("JOINED_{$ID}_$from_id", true);
                $seen = $funding->get("SEEN_$from_id") ?: [];
                if (!in_array($ID, $seen)) {
                    $seen[] = $ID;
                    $funding->set("SEEN_$from_id", $seen);
                }
                
                bot('answerCallbackQuery', [
                    'callback_query_id' => $update->callback_query->id,
                    'text' => "✅ بڕی $a3ml_الاشتراك $a3ml زیادکرا"
                ]);
                
                $funding->set("NOW_PRGRESS_" . $ID, $funding->get("NOW_PRGRESS_" . $ID) + 1);
                $current_progress = $funding->get("NOW_PRGRESS_" . $ID);
                
                bot('EditMessageReplyMarkup', [
                    'chat_id' => $OWNER,
                    'message_id' => $funding->get("MID_$ID"),
                    'reply_markup' => json_encode([
                        'inline_keyboard' => [
                            [["text" => "$current_progress/$COUNT", "callback_data" => "jgyugyj"]],
                        ]
                    ])
                ]);
                
                $Mtbqi = $COUNT - $current_progress;
                if (($wallets->get('notify_funding_' . $OWNER) ?? '✅') == '✅') {
                    bot('SendMessage', [
                        'chat_id' => $OWNER,
                        'reply_to_message_id' => $funding->get("MID_$ID"),
                        'text' => "*- کەسێکی نوێ جۆینی کەناڵەکەت بوو* [$CHANNEL] ➕

▫️  ژمارەی داواکراو : *$COUNT ئەندام*
▫️ژمارەی ماوە : *$Mtbqi ئەندام*
▫️ ژمارەی داواکاری : $ID

*🟥 لایمەبە [@$USRBOT] لە ئەدمینی بۆ بەردەوامبوونی ئەندام*",
                        'parse_mode' => 'Markdown',
                    ]);
                }
                
                if ($current_progress >= $COUNT) {
                    bot('SendMessage', [
                        'chat_id' => $OWNER,
                        'reply_to_message_id' => $funding->get("MID_$ID"),
                        'text' => "*ئەندامی کەناڵ تەواو بوو $CHANNEL* 🟢

▫️  ژمارەی داواکراو : *$COUNT ئەندام*
▫️ ژمارەی داواکاری : *$OLD_CH*
▫️ نرخی ئەندام : *$PRICE_TMOIL $a3ml*
",
                        'parse_mode' => 'Markdown',
                    ]);
                    
                    bot('SendMessage', [
                        'chat_id' => $ADMIN,
                        'text' => "*✅ ئاگاداری بۆ ئەدمین: ئەندام تەواو بوو*

📛 ناوی کەناڵ : $CHANNEL
👤 خاوەنی کەناڵ : [$OWNER](tg://user?id=$OWNER)

▫️  ژمارەی داواکراو : *$COUNT ئەندام*
▫️ ژمارەی داواکاری : *$OLD_CH*
▫️ نرخی ئەندام : *$PRICE_TMOIL $a3ml*
",
                        'parse_mode' => 'Markdown',
                    ]);
                    
                    $ids_raw = $funding->get("IDXS");
                    $idx_now = str_replace("$ID", "", $ids_raw);
                    $funding->set("IDXS", $idx_now);
                    $funding->delete('INFOS_' . $ID);
                    $funding->delete("NOW_PRGRESS_" . $ID);
                    $funding->delete('TMOIL_FOR_' . $CHANNEL);
                }
                
                $wallets->set('coins_' . $from_id, $wallets->get('coins_' . $from_id) + $a3ml_الاشتراك);
                $data = "JOIN_CHANNNELS";
            } else {
                bot('answerCallbackQuery', [
                    'callback_query_id' => $update->callback_query->id,
                    'text' => "❌ جۆینەکەت نەدۆزرایەوە، دڵنیابەرەوە لەوەی جۆینت کردووە"
                ]);
            }
        }
    }

} elseif (preg_match('/^SKIPCH_(.*)/', $data, $match)) {
    $ID = $match[1];
    
    $seen = $funding->get("SEEN_$from_id") ?: [];
    if (!in_array($ID, $seen)) {
        $seen[] = $ID;
        $funding->set("SEEN_$from_id", $seen);
    }

    bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "⏩ کەناڵەکە تێپەڕێندرا"
    ]);

    $GET_CH = GET_RANDOM_CH($from_id);
    if ($GET_CH) {
        $CH = explode("|", $GET_CH);
        $CHAN = $CH[0];
        $ID = $CH[1];
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'text' => "*جۆینی کەناڵی $CHAN بکە ✅*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "پشکنین ✅", "callback_data" => "CHKJOIN_$ID"]],
                    [["text" => "تێپەڕاندن ⏩", "callback_data" => "SKIPCH_$ID"], ["text" => "ڕاپۆرت ⛔️", "callback_data" => "REPORT_$ID"]],
                    [["text" => "🔙 گەڕانەوە", "callback_data" => "plus_coin"]],
                ]
            ])
        ]);
    } else {
        $data = "JOIN_CHANNNELS";
    }

} elseif (preg_match('/^REPORT_(.*)/', $data, $match)) {
    $ID = $match[1];
    
    $reports = $funding->get("REPORTS_$ID") ?: [];
    if (!in_array($from_id, $reports)) {
        $reports[] = $from_id;
        $funding->set("REPORTS_$ID", $reports);
    }

    $seen = $funding->get("SEEN_$from_id") ?: [];
    if (!in_array($ID, $seen)) {
        $seen[] = $ID;
        $funding->set("SEEN_$from_id", $seen);
    }
    $INFOS = $funding->get('INFOS_' . $ID);

    
    $parts = explode('|', $INFOS);
    list($COUNT, $PRICE_TMOIL, $CHANNEL, $OWNER) = array_pad($parts, 5, 'N/A');
    $Mtbqi = $funding->get("NOW_PRGRESS_" . $ID) ?? 1; 

    $ff = $users->get($OWNER) ?? "بەکارهێنەر نەناسراوە";

    $textd = "🔴 *ڕاپۆرتی دۆخی ئەندام*\n\n".
        "▫️*سەرچاوە:* کەناڵەکانی ئەندام\n".
        "▫️*زانیاری بەکارهێنەری ڕاپۆرتدەر:*\n".
        "- ناو: *$name*\n".
        "- ئایدی ژمارەیی: `$from_id`\n".
        "- یوزەر: [@$user]\n\n".
        "▫️*کەناڵی ئەندامکراو:* [$CHANNEL]\n".
        "▫️*ژمارەی ئەندامە نێردراوەکان:* *$Mtbqi* ئەندام\n".
        "▫️*ئەندامکراوە لەلایەن:* [$ff](tg://user?id=$OWNER)"; 
    bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "⛔️ ڕاپۆرتەکە نێردرا بۆ بەڕێوەبەرایەتی، سوپاس بۆ تۆ"
    ]);

    bot('SendMessage', [
        'chat_id' => $ADMIN,
        'text' => "$textd",
        'parse_mode' => 'Markdown', 
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "بلۆککردنی کەناڵ لە ئەندام", "callback_data" => "BLOCKTMOIL_$ID"]],
                [["text" => "هەڵوەشاندنەوەی ئەندام", "callback_data" => "CANCELTMOIL_$ID"]],
            ]
        ])
    ]); 

    $GET_CH = GET_RANDOM_CH($from_id);
    if ($GET_CH) {
        $CH = explode("|", $GET_CH);
        $CHAN = $CH[0];
        $ID = $CH[1];
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'text' => "*جۆینی کەناڵی $CHAN بکە ✅*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "پشکنین ✅", "callback_data" => "CHKJOIN_$ID"]],
                    [["text" => "تێپەڕاندن ⏩", "callback_data" => "SKIPCH_$ID"], ["text" => "ڕاپۆرت ⛔️", "callback_data" => "REPORT_$ID"]],
                    [["text" => "🔙 گەڕانەوە", "callback_data" => "plus_coin"]],
                ]
            ])
        ]);
    } else {
        $data = "JOIN_CHANNNELS";
    }
}

if($data == "JOIN_CHANNNELS" or $text == "/easy_get_channnnels"){
    $GET_CH = GET_RANDOM_CH($from_id);
    if($GET_CH){
        $CH = explode("|" , $GET_CH);
        $CHAN = $CH[0];
        $ID = $CH[1];
        if($data){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*جۆینی کەناڵی $CHAN بکە ✅*
",

        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "پشکنین ✅", "callback_data" => "CHKJOIN_$ID"]],
                [["text" => "تێپەڕاندن ⏩", "callback_data" => "SKIPCH_$ID"],["text" => "ڕاپۆرت ⛔️", "callback_data" => "REPORT_$ID"]],
                [["text" => "🔙 گەڕانەوە", "callback_data" => "plus_coin"]],
            ]
        ])
    ]);
}else{
    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => "$CHAN",
        'reply_markup' => json_encode([
        'inline_keyboard' => [
            [["text" => "نوێکردنەوە", "callback_data" => "upadte_easy"]],
        ]
    ])
    ]); 
    $sessions->set("UPDATEOR_$from_id" , $ID);
}
}else{
    if($data){
    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*🔴 هیچ کەناڵێک بەردەست نییە لە ئێستادا، دواتر هەوڵ بدەرەوە.*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "plus_coin"]],
            ]
        ])
    ]);
}else{
    bot('SendMessage', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*🔴 هیچ کەناڵێک بەردەست نییە لە ئێستادا، دواتر هەوڵ بدەرەوە.*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "نوێکردنەوە", "callback_data" => "upadte_easy"]],
            ]
        ])
    ]);

}
}
}

if($data == "upadte_easy"){
    bot('answerCallbackQuery', [
        'callback_query_id' => $update->callback_query->id,
    ]);
    
    $OLD_CH = $sessions->get("UPDATEOR_$from_id");
    $INFOS = $funding->get("INFOS_$OLD_CH");
    if ($INFOS) {
        list($COUNT, $PRICE_TMOIL, $CHANNEL, $OWNER) = explode('|', $INFOS);
    }
    $member = TMOIL(API_KEY, 'getChatMember', [
        'chat_id' => $CHANNEL,
        'user_id' => $from_id
    ]);
    $dataM = json_decode(json_encode($member), true);

    if ($dataM['ok'] && !in_array($dataM['result']['status'], ['left', 'kicked'])) {
        $sessions->delete("UPDATEOR_$from_id");
        $funding->set("NOW_PRGRESS_" . $OLD_CH ,$funding->get("NOW_PRGRESS_" . $OLD_CH) + 1);
        bot('EditMessageReplyMarkup', [
            'chat_id' => $OWNER,
            'message_id' => $funding->get("MID_$OLD_CH"),
            'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => $funding->get("NOW_PRGRESS_" . $OLD_CH) ."/$COUNT", "callback_data" => "jgyugyj"]],
            ]
        ])
        ]);
        bot('editMessageReplyMarkup',[
            'chat_id' => $OWNER,
            'message_id'=>$funding->get("MID_$ID"),
            'inline_message_id'=>$message_id->inline_query->inline_message_id,
            'reply_markup'=>json_encode([
            'inline_keyboard'=>[
                [["text" => $funding->get("NOW_PRGRESS_" . $OLD_CH) ."/$COUNT", "callback_data" => "jgyugyj"]],
            ]])
            ]);
            if($funding->get("NOW_PRGRESS_" . $OLD_CH) >= $COUNT){
                bot('SendMessage', [
                    'chat_id' => $OWNER,
                    'reply_to_message_id' => $funding->get("MID_$OLD_CH"),
                    'text' => "*ئەندامی کەناڵ تەواو بوو $CHANNEL* 🟢

▫️  ژمارەی داواکراو : *$COUNT ئەندام*
▫️ ژمارەی داواکاری : *$OLD_CH*
▫️ نرخی ئەندام : *$PRICE_TMOIL $a3ml*
",
                    'parse_mode' => 'Markdown', 
                ]); 
                bot('SendMessage', [
                    'chat_id' => $ADMIN,
                    'text' => "*✅ ئاگاداری بۆ ئەدمین: ئەندام تەواو بوو*

📛 ناوی کەناڵ : $CHANNEL
👤 خاوەنی کەناڵ : [$OWNER](tg://user?id=$OWNER)

▫️  ژمارەی داواکراو : *$COUNT ئەندام*
▫️ ژمارەی داواکاری : *$OLD_CH*
▫️ نرخی ئەندام : *$PRICE_TMOIL $a3ml*
",
                    'parse_mode' => 'Markdown', 
                ]);

                $ids_raw = $funding->get("IDXS");
                $idx_now = str_replace("$OLD_CH" , "" , $ids_raw );
                $funding->set("IDXS" , $idx_now );
                $funding->delete('INFOS_' . $OLD_CH);
                $funding->delete("NOW_PRGRESS_" . $OLD_CH);
                $funding->delete('TMOIL_FOR_'. $CHANNEL);
            }
    }
    $GET_CH = GET_RANDOM_CH($from_id);
    if($GET_CH){
    $CH = explode("|" , $GET_CH);
    $CHAN = $CH[0];
    $ID = $CH[1];
bot('EditMessageText', [
    'chat_id' => $chat_id, 
    'message_id' => $message_id,
    'text' => "$CHAN
",
'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "نوێکردنەوە", "callback_data" => "upadte_easy"]],
            ]
        ])
]);
$sessions->set("UPDATEOR_$from_id" , $ID);
    }else{
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'text' => "*🔴 هیچ کەناڵێک بەردەست نییە لە ئێستادا، دواتر هەوڵ بدەرەوە.*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "نوێکردنەوە", "callback_data" => "upadte_easy"]],
                ]
            ])
        ]);
    }
}
if ($data == 'TMOILOS') {
    $S_LIST = ['inline_keyboard' => []];
    $النص = "*🌟 هەموو ئەو کەناڵ و گرووپانەی کە ئێستا ئەندامیان دەکەیت:*
لەم پەڕەیەدا هەموو ئەو کەناڵ و گرووپانەت بۆ دەردەکەوێت کە ئەندامت کردوون، و دەتوانیت بە ئاسانی چاودێریان بکەیت.
";

    $ids_raw = $funding->get("IDXS_$from_id");


    $ids = explode("\n", trim($ids_raw));
    shuffle($ids);

    $checked_channels = [];
    $OK = 0;

    foreach ($ids as $id) {
        $INFOS = $funding->get('INFOS_' . $id);
        if (!$INFOS) continue;

        $parts = explode('|', $INFOS);
        $NOWMEM = $funding->get("NOW_PRGRESS_" . $id) ?? 0;
        list($COUNT, $PRICE_TMOIL, $CHANNEL, $OWNER) = array_pad($parts, 4, 'N/A');
        $S_LIST['inline_keyboard'][] = [
            ['text' => "$CHANNEL", 'callback_data' => "STATUS_$id"],
            ['text' => "$NOWMEM/$COUNT", 'callback_data' => "STATUS_$id"]
        ];
        $OK = 1;
    }

    if (!$OK) {
        $Sok = "🔻 هیچ کەناڵێک نییە لە ئێستادا"; 
    } else {
        $Sok = "🔄 نوێکردنەوەی لیست";
    }

    $S_LIST['inline_keyboard'][] = [['text' => "$Sok", 'callback_data' => "TMOILOS"]];
    $S_LIST['inline_keyboard'][] = [['text' => "🔙 گەڕانەوە", 'callback_data' => "BACK"]];

    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "$النص",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode($S_LIST)
    ]);
}



if($data == 'TMOIL_x'){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "️️⚠️ یاساکانی گەشەپێدانی کەناڵەکەت:

▪️ کەناڵی پریڤایت نابێت ❌.
▪️کەناڵی پۆستی نەشیاو نابێت ❌.
▪️ گۆڕینی یوزەر کەناڵ نابێت ❌.
▪️ جۆین کەناڵ بە ڕیکوێست نابێت ❌.
▪️ بۆت لە ئەدمین لامەبە نابێت ❌.

🔴 سەرپێچی = هەڵوەشاندنەوەی کەناڵەکەت",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "زیادکردنی ئەندام 🚀", "callback_data" => "MAKE_TMOIL"]],
                [["text" => "ئەنجامدانی جۆین 📣", "callback_data" => "JOIN_CHANNNELS"],
                ["text" => "تۆماری کەناڵەکان 📃", "callback_data" => "TMOILOS"]],
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACK"]],
            ]
        ])
    ]);
    $sessions->delete('mode_'.$from_id);
}

if($data == "MAKE_TMOIL"){
    $سعر_الف = $سعر_تمويل * 1000;
    $tmoil_min = $bot->get('tmoil_min') ?? "10";
    $tmoil_max = $bot->get('tmoil_max') ?? "5000";

    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*🔲 ژمارەی ئەو ئەندامانە بنێرە کە دەتەوێت داوایان بکەیت*

📉 کەمترین ژمارە: *$tmoil_min*
📈 زۆرترین ژمارە: *$tmoil_max*

▫️ نرخی هەر 1 ئەندام = *$سعر_تمويل $a3ml*
◼️ نرخی هەر 1000 ئەندام = *$سعر_الف $a3ml*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "TMOIL_x"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id , $data);
}

if($text and $sessions->get('mode_'.$from_id) == "MAKE_TMOIL"){
    if(is_numeric($text)){
        $tmoil_min = $bot->get('tmoil_min') ?? 10;
        $tmoil_max = $bot->get('tmoil_max') ?? 5000;

        if($text < $tmoil_min){
            bot('SendMessage', [
                'chat_id' => $chat_id,
                'text' => "*❌ ژمارەی داواکراو کەمترە لە کەمترین بڕ!*\nبڕی کەمترین: $tmoil_min",
                'parse_mode' => 'Markdown',
            ]);
            return;
        }
        if($text > $tmoil_max){
            bot('SendMessage', [
                'chat_id' => $chat_id,
                'text' => "*❌ ژمارەی داواکراو زیاترە لە زۆرترین بڕ!*\nبڕی زۆرترین: $tmoil_max",
                'parse_mode' => 'Markdown',
            ]);
            return;
        }

        $userbot = json_decode(file_get_contents("https://api.telegram.org/bot" . API_KEY ."/getme"))->result->username;
        $PRICE_ME = $text * $سعر_تمويل;
        $coins = $wallets->get('coins_'.$chat_id);
        
        if($coins >= $PRICE_ME){
            bot('SendMessage', [
    'chat_id' => $chat_id,
    'text' => "✅ *داواکاری بۆ $text ئەندام وەرگیرا*
💰 *نرخ:* $PRICE_ME $a3ml

⚠️ *مەرجی سەرەکی:*
سەرەتا بۆت بکە بە ئەدمین 👉 [@$userbot]
دواتر یوزەری کەناڵەکەت بنێرە 👇",
    'parse_mode' => 'Markdown',
    'reply_markup' => json_encode([
        'inline_keyboard' => [
            [["text" => "🔙 گەڕانەوە", "callback_data" => "TMOIL_x"]],
        ]
    ])
]);
            $sessions->set('mode_'.$from_id , "NEED_CHANNEL");
            $sessions->set('helper_'.$from_id , "$text");
            return;
        }else{
            bot('SendMessage', [
                'chat_id' => $chat_id,
                'text' => "*خاڵەکانت بەش ناکات 🔴*

نرخی ئەم ئەندامە دەکاتە : *$PRICE_ME $a3ml*",
                'parse_mode' => 'Markdown',
                'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "🔙 گەڕانەوە", "callback_data" => "TMOIL_x"]],
                ]
            ])
            ]); 
        }
    }
}

function CHECKIFADMIN($text, $token = API_KEY) {
    global $bot_id;
    // نفترض أن دالة TMOIL تعيد كائن (object)
    $channel_info = TMOIL($token, 'getChat', ['chat_id' => $text]);

    if (isset($channel_info->ok) && $channel_info->ok) {
        $member_info = TMOIL($token, 'getChatMember', [
            'chat_id' => $text,
            'user_id' => $bot_id
        ]);

        if (isset($member_info->ok) && $member_info->ok && in_array($member_info->result->status, ['administrator', 'creator'])) {
            return true;
        }
    }

    return false;
}

function generatePrettyNumbers($count = 1) {
    $numbers = [];
    $attempts = 0;
    $maxAttempts = 500; 

    while (count($numbers) < $count && $attempts < $maxAttempts) {
        $num = str_pad(random_int(0, 999999), 6, '0', STR_PAD_LEFT);
        if (isPretty($num) && !in_array($num, $numbers)) {
            $numbers[] = $num;
        }
        $attempts++;
    }
    
    if (empty($numbers)) {
        $numbers[] = str_pad(random_int(0, 999999), 6, '0', STR_PAD_LEFT);
    }

    return $numbers;
}

function isPretty($num) {
    return (
        preg_match('/^(.)\1{5}$/', $num) ||                   
        preg_match('/^(\d)\1{2}(\d)\2{2}$/', $num) ||          
        preg_match('/^(\d)(\d)\1\2\1\2$/', $num) ||               
        preg_match('/^123456|654321|112233|223344$/', $num) ||  
        preg_match('/^(\d)(\d)(\d)\3\2\1$/', $num)               
    );
}

if ($text and $sessions->get('mode_' . $from_id) == "NEED_CHANNEL") {


    $blocklist = $bot->get('funding_blocklist') ?? [];
    if (in_array(strtolower($text), array_map('strtolower', $blocklist))) {
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => "🚫 *ئەم کەناڵە لە ئەندام بلۆک کراوە و ناتوانرێت داواکاری بۆ بکرێت*",
            'parse_mode' => 'Markdown'
        ]);
        return;
    }
    if (preg_match('/^@[\w_]{5,}$/', $text)) {
        if (CHECKIFADMIN($text)) {

            if(!$funding->get('TMOIL_FOR_'. $text)){
               
                $LAST_PENDING = $funding->get("lastid_tmoil_" . $from_id);
                if ($LAST_PENDING) {
                    $funding->delete("INFOS_" . $LAST_PENDING);
                }

                $prettyNumbers = generatePrettyNumbers(1);
                $IDX = $prettyNumbers[0]; 

                $COUNT = $sessions->get('helper_' . $from_id);
                $PRICE_TMOIL = $COUNT * $سعر_تمويل;

                bot('SendMessage', [
                    'chat_id' => $chat_id,
                    'text' => "*🔹 زانیاری پێش دروستکردنی ئەندامەکەت*\n\n🔸 داوای : *$COUNT ئەندام* دەکەیت\n🔸 نرخی ئەندام : *$PRICE_TMOIL $a3ml*\n🔸 بۆ کەناڵی : [$text]\n🔸 ژمارەی داواکاری : `$IDX`",
                    'parse_mode' => 'Markdown',
                    'reply_markup' => json_encode([
                        'inline_keyboard' => [
                            [["text" => "دروستکردنی ئەندام ✅", "callback_data" => "MAKKER_TMOIL_$IDX"]],
                            [["text" => "هەڵوەشاندنەوەی ئەندام ❌", "callback_data" => "cancel_tmoil_$IDX"]],
                        ]
                    ])
                ]);
                
                $funding->set('lastid_tmoil_' . $chat_id, "$IDX");
                $funding->set('INFOS_' . $IDX, "$COUNT|$PRICE_TMOIL|$text|$chat_id");
                
                $sessions->delete('mode_' . $from_id);
            } else {
                bot('sendMessage', [
                    'chat_id' => $chat_id,
                    'parse_mode' => 'Markdown',
                    'text' => "*ببورە بەڵام کەناڵەکە لەژێر ئەندام دایە ✅*\n♻️ چاوەڕێ بکە تا *ئەندام تەواو دەبێت* و دووبارە هەوڵ بدەرەوە .",
                    'reply_markup' => json_encode([
                        'inline_keyboard' => [
                            [["text" => "گەڕانەوە ❌", "callback_data" => "MAKE_TMOIL"]],
                        ]
                    ])
                ]);
                $sessions->delete('mode_' . $from_id);
            }
        } else {
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => "❗️ دڵنیابەرەوە کە بۆتەکە ئەدمینە لە کەناڵەکە پێش بەردەوام بوون.",
            ]);
        }
    } else {
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => "❗️ تکایە یوزەری کەناڵ بنێرە کە بە @ دەست پێبکات .",
        ]);
    }
}

$MAKKER_TMOIL_= explode("MAKKER_TMOIL_" , $data)[1];
if($MAKKER_TMOIL_){
    $INFOS = $funding->get('INFOS_' . $MAKKER_TMOIL_);
    $S_TEXT = explode('|', $INFOS);
    list($COUNT , $PRICE_TMOIL , $CHANNEL , $OWNER) = array_pad($S_TEXT, 3, 'N/A');
    $coins = $wallets->get('coins_'.$chat_id);
    if($coins >= $PRICE_TMOIL){
        bot('answerCallbackQuery', [
            'callback_query_id' => $update->callback_query->id,
            'text' => "داواکارییەکی نوێی ئەندام دروستکرا ✅",
            'show_alert' => true,
        ]);
        $coinsor = $wallets->get('coins_'.$chat_id) ?? "0";
        $coinsleft = $wallets->get('coinsuseed_'.$from_id) ?? "0";
        $hdaiacount = $wallets->get('hdiacoins_'.$from_id) ?? "0";
        $hdiacountx =$wallets->get('hdiax_'.$from_id) ?? "0";
        $transers = $wallets->get('transcoins_'.$from_id) ?? "0";
        $i_trans = $wallets->get('transsucces_'.$from_id)  ?? "0";
        $invits_count = $wallets->get('countshare_'.$from_id) ?? "0";
        $coinsmeshare = $wallets->get('coinsshare_'.$from_id) ?? "0";
        $NOW_NQAT = $coinsor - $PRICE_TMOIL;
        $ish3ar_tmoil = $bot->get('shi3ar_tmoil') ?? '✅';
        if($ish3ar_tmoil == '✅'){
            bot('SendMessage', [
                'chat_id' => $ADMIN, 
                'text' => "*ئەندامی کەناڵێک دەستی پێکرد لە بۆتەکەت ✅*

♻️ ئەندام بۆ : [$CHANNEL]
♻️ ژمارەی ئەندام : *$COUNT ئەندام*
♻️ نرخی ئەندام : *$PRICE_TMOIL $a3ml*
♻️ ژمارەی داواکاری : `$MAKKER_TMOIL_`

*👤 زانیاری کەسەکە:*
• *ناو:* [$name](tg://user?id=$from_id)
• *ئایدی:* `$from_id`
• *یوزەر:* [@$user]
• *ژمارەی $a3ml:* $coinsor
• *$a3ml ی بەکارهێنراو:* $coinsleft
• *$a3ml ی دیاری:* $hdaiacount
• *ژمارەی بانگهێشت:* $invits_count
• *$a3ml لە بەستەری بڵاوکردنەوە:* $coinsmeshare

• *بووە خاوەنی ".$a3ml." :* $NOW_NQAT",
                'parse_mode' => 'Markdown',
                'reply_markup' => json_encode([
                        'inline_keyboard' => [
                            [["text" => "بلۆککردنی کەناڵ لە ئەندام", "callback_data" => "BLOCKTMOIL_$MAKKER_TMOIL_"]],
                            [["text" => "هەڵوەشاندنەوەی ئەندام", "callback_data" => "CANCELTMOIL_$MAKKER_TMOIL_"]],
                        ]
                    ])
            ]);
        }
        bot('EditMessageText', [
            'chat_id' => $chat_id, 
            'message_id' => $message_id,
            'text' => "*🟢 داواکارییەکی نوێی ئەندام دروستکرا *

🔘 ئەندام بۆ : [$CHANNEL]
🔘 ژمارەی ئەندام : *$COUNT ئەندام*
🔘 نرخی ئەندام : *$PRICE_TMOIL $a3ml*
🔘 ژمارەی داواکاری : `$MAKKER_TMOIL_`",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                    'inline_keyboard' => [
                        [["text" => "0/$COUNT", "callback_data" => "STATUS_$MAKKER_TMOIL_"]],
                    ]
                ])
        ]);

        $wallets->set('coinsuseed_'.$from_id, $wallets->get('coinsuseed_'.$from_id) + $PRICE_TMOIL);

        $wallets->set('coins_'.$from_id,$wallets->get('coins_'.$from_id) - $PRICE_TMOIL);
        $funding->set("MID_$MAKKER_TMOIL_" , $message_id);
        $funding->set('TMOIL_FOR_'. $CHANNEL , true);
        $funding->set("IDXS" , $funding->get("IDXS") . "\n" . $MAKKER_TMOIL_);
        $funding->set("IDXS_$from_id" , $funding->get("IDXS_$from_id") . "\n" . $MAKKER_TMOIL_);
        
        $funding->delete('lastid_tmoil_' . $from_id);

        $sessions->delete('mode_' . $from_id);
    }else{
        bot('EditMessageText', [
            'chat_id' => $chat_id, 
            'message_id' => $message_id,
            'text' => "*🔴 ببورە ئازیزم $a3ml ت بەش ناکات بۆ دروستکردنی ئەندام*

🟢 نرخی ئەم ئەندامە : *$PRICE_TMOIL $a3ml*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "هەڵوەشاندنەوە 🔴", "callback_data" => "cancel_tmoil_$MAKKER_TMOIL_"]],
                ]
            ])
        ]);
    }
}

$BLOCKTMOIL_ = explode("BLOCKTMOIL_" , $data)[1];
if($BLOCKTMOIL_){
    $data = "CANCELTMOIL_". $BLOCKTMOIL_; 
    $OKL = true;
}

$CANCELTMOIL_ = explode("CANCELTMOIL_" , $data)[1];
if($CANCELTMOIL_){
        $INFOS = $funding->get('INFOS_' . $CANCELTMOIL_);
        if ($INFOS) { 
            $S_TEXT = explode('|', $INFOS);
            list($COUNT , $PRICE_TMOIL , $CHANNEL , $OWNER) = array_pad($S_TEXT, 4, 'N/A');
            $MID = $funding->get("MID_$CANCELTMOIL_");
            $SVT = str_replace($CANCELTMOIL_ , '' , $funding->get("IDXS"));
            $funding->set("IDXS" , $SVT);
            
            $CVT = str_replace($CANCELTMOIL_ , '' , $funding->get("IDXS_$OWNER"));
            $funding->set("IDXS_$OWNER" , $CVT);

            $funding->delete('INFOS_' . $CANCELTMOIL_);
            $funding->delete('TMOIL_FOR_'. $CHANNEL);
            bot('editMessageReplyMarkup',[
                'chat_id' => $OWNER,
                'message_id'=>$MID,
                'inline_message_id'=>$message_id->inline_query->inline_message_id,
                'reply_markup'=>json_encode([
                'inline_keyboard'=>[
                    [["text" => "داواکاری ئەندامەکەت هەڵوەشێندرایەوە لەلایەن بەڕێوەبەرایەتی", "url" => "https://t.me/" . str_replace('@','',$CHANNEL)]],
                    [["text" => "هەژماری بەڕێوەبەرایەتی ✅", "url" => "tg://user?id=$ADMIN"]],
                ]])
                ]);
                bot('editMessageReplyMarkup',[
                'chat_id' => $chat_id,
                'message_id'=>$message_id,
                'inline_message_id'=>$message_id->inline_query->inline_message_id,
                'reply_markup'=>json_encode([
                'inline_keyboard'=>[
                    [["text" => "کەناڵەکە لە ئەندام لابرا", "url" => "https://t.me/" . str_replace('@','',$CHANNEL)]],
                ]])
                ]);
                if(!$OKL){
            bot('answerCallbackQuery', [
            'callback_query_id' => $update->callback_query->id,
            'text' => "ئەندامی کەناڵی $CHANNEL هەڵوەشێندرایەوە ✅",
            'show_alert' => true,
        ]);
    }else{
        bot('answerCallbackQuery', [
            'callback_query_id' => $update->callback_query->id,
            'text' => "ئەندامی کەناڵی $CHANNEL هەڵوەشێندرایەوە + بلۆک کرا ✅",
            'show_alert' => true,
        ]);
    }
        $funding->delete("MID_$CANCELTMOIL_");
    }
}

$cancel_tmoil_ = explode("cancel_tmoil_" , $data)[1];
if($cancel_tmoil_){
    bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "داواکاری ئەندام هەڵوەشێندرایەوە ❎",
        'show_alert' => true,
    ]);
    $sessions->delete('mode_'.$from_id);
    $funding->delete('INFOS_' . $cancel_tmoil_);
    
    $funding->delete('lastid_tmoil_' . $from_id);
    
    $data = 'BACK';
}


if ($data == 'my_tlbs') {
    $my_orders_string = $wallets->get('MYORDERSTEXT_' . $from_id);

    $my_orders_string = trim($my_orders_string);

    if (empty($my_orders_string)) {
        bot('answerCallbackQuery', [
            'callback_query_id' => $update->callback_query->id,
            'text' => "هیچ داواکارییەکی تۆمارکراوت نییە.",
            'show_alert' => true,
        ]);
        return;
    }

    $parts = preg_split('/(?=• (داواکاری|داواکاری) :)/u', $my_orders_string, -1, PREG_SPLIT_NO_EMPTY);
    $all_orders = array_values(array_filter(array_map('trim', $parts)));

    $total_orders = count($all_orders);
    $last_five_orders = ($total_orders > 5) ? array_slice($all_orders, -5) : $all_orders;
    
    $display_text = "*📨 دوایین 5 داواکاریت:*\n\n";
    $display_text .= implode("\n------------------------------\n", $last_five_orders);

    if (strlen($display_text) > 4000) {
        $display_text = mb_substr($display_text, 0, 4000, 'UTF-8') . "\n...";
    }

    $keyboard = [
        'inline_keyboard' => [
            [['text' => "📥 دەرکردنی هەموو داواکارییەکان (فایل)", 'callback_data' => "export_my_orders"]],
            [['text' => "🔙 گەڕانەوە", 'callback_data' => "BACK"]]
        ]
    ];

    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => $display_text,
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode($keyboard)
    ]);
}

if ($data == 'export_my_orders') {
    $my_orders_string = $wallets->get('MYORDERSTEXT_' . $from_id);
    
    if (empty(trim($my_orders_string))) {
         bot('answerCallbackQuery', [
            'callback_query_id' => $update->callback_query->id,
            'text' => "هیچ داواکارییەکت نییە بۆ دەرکردن.",
            'show_alert' => true,
        ]);
        return;
    }
    
    $filename = "my_orders_{$from_id}.txt";
    file_put_contents($filename, "--- هەموو داواکارییەکانت ---\n\n" . $my_orders_string);

    bot('sendDocument', [
        'chat_id' => $chat_id,
        'document' => new CURLFile(realpath($filename)),
        'caption' => "ئەمە فایلێکە کە هەموو داواکارییەکانتی تێدایە."
    ]);

    unlink($filename);
    
    bot('answerCallbackQuery', [
        'callback_query_id' => $update->callback_query->id,
    ]);
}

if($data == "cancel"){
    bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "داواکاری هەڵوەشێندرایەوە ❎",
        'show_alert' => true,
    ]);
    $sessions->delete('mode_'.$from_id);
    $sessions->delete('xdma_'.$from_id);
    $sessions->delete('count_'.$from_id);
    $sessions->delete('link_'.$from_id);
    $data = 'BACK';
}

$cancel_tmoil_ = explode("cancel_tmoil_" , $data)[1];
if($cancel_tmoil_){
    bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "داواکاری ئەندام هەڵوەشێندرایەوە ❎",
        'show_alert' => true,
    ]);
    $sessions->delete('mode_'.$from_id);
    $funding->delete('INFOS_' . $cancel_tmoil_);
    $data = 'BACK';
}
            

if($data == "count_orders"){
    $count_services = $bot->get('ORDERS') ?? "0";
    bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "ژمارەی داواکارییە تەواوبووەکان : $count_services ✅",
        
    ]);
    $data = 'BACK';
}

if($data == 'BACK'){
    $count_services = $bot->get('ORDERS') ?? "0";
    $ALASASE = $bot->get('zrar_alasase');
    $inline_keyboard = [];
    $a3ml = $bot->get("currency") ?: "خاڵ";

    if ($ALASASE == '✅') {
        if(($bot->get('B_STATUS_SERVICES') ?: '✅') != '❌'){
            $inline_keyboard[] = [["text" => "خزمەتگوزارییەکان 🛒", "callback_data" => "SERVICES"]];
        }
        if(($bot->get('B_STATUS_TMOIL_x') ?: '✅') != '❌'){
            $inline_keyboard[] = [["text" => "گەشەپێدانی کەناڵەکەت 📣", "callback_data" => "TMOIL_x"]];
        }
        
        $row_money = [];
        if(($bot->get('B_STATUS_plus_coin') ?: '✅') != '❌') $row_money[] = ["text" => "❇️ کۆکردنەوە", "callback_data" => "plus_coin"];
        if(($bot->get('B_STATUS_transfer_coin') ?: '✅') != '❌') $row_money[] = ["text" => "🔁 گواستنەوەی $a3ml", "callback_data" => "transfer_coin"];
        if(!empty($row_money)) $inline_keyboard[] = $row_money;

        $row_acc = [];
        if(($bot->get('B_STATUS_use_code') ?: '✅') != '❌') $row_acc[] = ["text" => "💳 بەکارهێنانی کۆد", "callback_data" => "use_code"];
        if(($bot->get('B_STATUS_acount_me') ?: '✅') != '❌') $row_acc[] = ["text" => "👤 هەژمار", "callback_data" => "acount_me"];
        if(!empty($row_acc)) $inline_keyboard[] = $row_acc;

        $row_orders = [];
        if(($bot->get('B_STATUS_my_tlbs') ?: '✅') != '❌') $row_orders[] = ["text" => "📨 داواکارییەکانم", "callback_data" => "my_tlbs"];
        if(($bot->get('B_STATUS_info_tlb') ?: '✅') != '❌') $row_orders[] = ["text" => "📬 زانیاری داواکاری", "callback_data" => "info_tlb"];
        if(!empty($row_orders)) $inline_keyboard[] = $row_orders;

        $row_stats = [];
        if(($bot->get('B_STATUS_sh7n') ?: '✅') != '❌') $row_stats[] = ["text" => "💸 کڕینی $a3ml", "callback_data" => "sh7n"];
        if(($bot->get('B_STATUS_stats') ?: '✅') != '❌') $row_stats[] = ["text" => "📊 ئامارەکان", "callback_data" => "stats"];
        if(!empty($row_stats)) $inline_keyboard[] = $row_stats;

        $row_info = [];
        if(($bot->get('B_STATUS_bot_help') ?: '✅') != '❌') $row_info[] = ["text" => "⁉️ ڕوونکردنەوە", "callback_data" => "bot_help"];
        if(($bot->get('B_STATUS_aggrement') ?: '✅') != '❌') $row_info[] = ["text" => "📝 مەرجەکان", "callback_data" => "aggrement"];
        if(!empty($row_info)) $inline_keyboard[] = $row_info;

        if(($bot->get('B_STATUS_count_orders') ?: '✅') != '❌'){
            $inline_keyboard[] = [["text" => "✅ ژمارەی داواکارییەکان : $count_services ✅", "callback_data" => "count_orders"]];
        }
    }

    $lines_text = "";
    for ($i = 1; $i <= 20; $i++) {
        $gg = $bot->get("zrs_IN_LINE_$i");
        if ($gg) {
            $lines_text .= $gg . "[in_$i]\n";
        }
    }

    $lines = explode("\n", $lines_text);

    foreach ($lines as $line) {
        preg_match_all('/\[(.*?)\]/', $line, $matches);
        $row = [];

        foreach ($matches[1] as $btn_text) {
            $tt = store_text($btn_text);
            $GG = $bot->get("zrs_info_$btn_text");
            $THDATA = $bot->get("zrs_info_content_$btn_text");

            if ($GG == '【Link / بەستەر】') {
                $UU = 'url';
            } elseif ($GG == '【Text / ناوەڕۆکی دەقی】') {
                $UU = 'callback_data';
                $THDATA = "viewAzd_" . getencode($btn_text);
            } elseif ($GG == '【Shortcut / دوگمەی کورتکراوە】') {
                $UU = 'callback_data';
                $CODE = explode('BB:', $THDATA)[1];
                $THDATA = base64_decode(base64_decode(base64_decode($CODE)));
            } else {
                continue; 
            }

            $row[] = [
                "text" => "$btn_text",
                "$UU" => "$THDATA",
            ];
        }

        if (!empty($row)) {
            $inline_keyboard[] = $row;
        }
    }
    if(in_array($chat_id, $ADMINS)){
        $inline_keyboard[] = [["text" => "🎛 پانێڵی بەڕێوەبەر", "callback_data" => "GOTO_ADMIN_PANEL"]];
    }
    
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "$START",
        'parse_mode' => 'html',
        'disable_web_page_preview' => true,
        'reply_markup' => json_encode(['inline_keyboard' => $inline_keyboard])
    ]);
    
    $sessions->delete('mode_'.$from_id);
}

if (isset($from_id) && isset($chat_type) && $chat_type == 'private') {
    $cache->set('last_active_' . $from_id, time());

    $current_day = date('d');
    $current_month = date('Y-m'); 
 
    $user_daily_activity_key = 'IN_ACTIVE_' . $from_id . '_' . $current_day;

    if (!$cache->get($user_daily_activity_key)) {
        
        $cache->set($user_daily_activity_key, true);

        if ($stats->get('day') != $current_day) {
            $stats->set('day', $current_day);
            $stats->set('activers_today', 1);
        } else {
            $stats->set('activers_today', (int)$stats->get('activers_today') + 1);
        }

        if ($stats->get('month') != $current_month) { // 
            $stats->set('month', $current_month);
            $stats->set('activers_MONTH', 1);
        } else {
            $stats->set('activers_MONTH', (int)$stats->get('activers_MONTH') + 1);
        }
    }
}


if ($data == "stats") {
    $count_services = $bot->get('ORDERS') ?? "0";
    $ACTIVER_TODAY = $stats->get('activers_today') ?? "0";
    $ACTIVER_MONTH = $stats->get('activers_MONTH') ?? "0";
    
    $all_users = $users->getAllWithPrefix('');
    $MEMS = count($all_users) + ($FAKEOS ?? 0);
    
    $CHSx = count(array_filter(explode("\n", $funding->get("IDXS")), fn($line) => trim($line) !== ''));

    $active_now_count = 0;
    $time_frame = 300;
    $all_active_users_cache = $cache->getAllWithPrefix('last_active_');
    foreach ($all_active_users_cache as $key => $last_active_timestamp) {
        if ($last_active_timestamp && (time() - $last_active_timestamp) <= $time_frame) {
            $active_now_count++;
        }
    }
    
    $topRefs = $referral_system->get('top_refs') ?? [];
    arsort($topRefs);
    $top10 = array_slice($topRefs, 0, 5, true);
    $medals = ["🥇", "🥈", "🥉"];
    
    $H = ''; 
    $rank = 0;
    foreach ($top10 as $id => $count) {
        if (is_numeric($id)) {
            $user_name = $users->get($id) ?? $id;            $emoji = $medals[$rank] ?? "🎖️";
            $H .= "• [$user_name](tg://user?id=$id) ($count)$emoji\n";
            $rank++;
        }
    }

    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "*📊 ئامارە گشتییەکانی بۆت

👥 سەرجەم بەکارهێنەران: $MEMS
🟢 چالاکی ئێستا: $active_now_count
📅 چالاکی ئەمڕۆ: $ACTIVER_TODAY
🗓 چالاکی ئەم مانگە: $ACTIVER_MONTH

✅ داواکارییە تەواوبووەکان: $count_services
⏳ کەناڵەکان لە پڕۆسەی زیادکردن ئەندام: $CHSx

🏆 بەرزترینەکان لە بانگهێشتکردن:
*    
$H",
        'parse_mode' => 'Markdown',
        'disable_web_page_preview' => true,
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACK"]],
            ]
        ])
    ]);
}

if($data == 'info_tlb'){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*تکایە ئایدی داواکاری بنێرە 🔣*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACK"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id,$data);
}

if($text and $sessions->get('mode_'.$from_id) == 'info_tlb'){
    $get_order = $orders->get($text);
    $S_TEXT = explode('|', $get_order);

    list($API , $DOMIN, $xdma ,$TO, $count, $price,$owner) = array_pad($S_TEXT, 12, 'N/A');
    if($DOMIN && $API){
        if($owner == $from_id){
        $G = json_decode(file_get_contents("https://$DOMIN/api/v2?key=$API&action=status&order=$text"))->status;
        if($G){
            bot('SendMessage', [
                'chat_id' => $chat_id,
                'text' => "*زانیاری داواکاری* `$text` ✅
*• ناوی خزمەتگوزاری :* $xdma 🔤
*• دۆخ :* $G ✳️
*• نرخ :* $price $a3ml 💰
*• بڕ :* $count ⛓️

*• داواکراوە بۆ :* `$TO` 💡
",
                'parse_mode' => 'Markdown',
                'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "🔙 گەڕانەوە", "callback_data" => "BACK"]],
                ]
            ])
            ]); 
            $sessions->delete('mode_'.$from_id);
        }else{
            bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*ئایدی داواکاری هەڵەیە ❌*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACK"]],
            ]
        ])
        ]); 
        }
        } else{
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*ئەم داواکارییە لە ناو داواکارییەکانی تۆ نەدۆزرایەوە ❎*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACK"]],
            ]
        ])
        ]);  
        }
    }else{
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*ئایدی داواکاری هەڵەیە ❌*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACK"]],
            ]
        ])
        ]); 
    }
}
function rand_text(){
    $abc = array("a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z","1","2","3","4","5","6","7","8","9","0");
    $fol = '#'.$abc[rand(5,36)].$abc[rand(5,36)].$abc[rand(5,36)].$abc[rand(5,36)].$abc[rand(5,36)].$abc[rand(5,36)].$abc[rand(5,36)].$abc[rand(5,36)].$abc[rand(5,36)].$abc[rand(5,36)];
    return $fol;
}
function Invoice($amount ,$amounter ) {
    global $name_bot , $a3ml;
    $data = [
        'title' => "کرداری کڕینی $amounter $a3ml",
        'description' => "زانیاری پارەدان:",
        'payload' => rand_text(),
        'provider_token' => '', 
        'currency' => 'XTR',
        'prices' => json_encode([['amount' => $amount, 'label' => '1']]),
    ];

    $response = bot('createInvoiceLink', $data);

    return $response->result;
}


    if($data == 'sh7n'){
        $payed_text = $bot->get('payed') ?? "دیاری نەکراوە";
        $agents = $bot->get("agents") ?? [];
        $buttons = [];
        foreach ($agents as $agent) {
            if(preg_match('/https/',$agent["link"])){
            $buttons[] = [["text" => $agent["name"], "url" => $agent["link"]],
            ];
        }
        }
        $payment_methods = [];
        if($bot->get('AL_NJOM_x') == '✅'){
            $payment_methods [] = ["text" => "ئەستێرە ⭐", "callback_data" => "KM_TRID_AN_TSH7n"];
        }
        if($bot->get('AL_FASTPAY_x') == '✅'){
            $payment_methods [] = ["text" => "فاستپەی ⚡", "callback_data" => "BUY_WITH_FASTPAY"];
        }
        if($bot->get('AL_FIB_x') == '✅'){
            $payment_methods [] = ["text" => "ئیف ئای بێ 🏦", "callback_data" => "BUY_WITH_FIB"];
        }
        if($bot->get('AL_ASIACELL_x') == '✅'){
            $payment_methods [] = ["text" => "ئاسیاسێڵ 📞", "callback_data" => "BUY_WITH_ASIACELL"];
        }
        $rows = array_chunk($payment_methods, 2);

    foreach($rows as $row){
        $buttons[] = $row;
    }
        $buttons[] = [["text" => "🔙 گەڕانەوە", "callback_data" => "BACK"]];
    bot('EditMessageText', [
            'chat_id' => $chat_id, 
            'message_id' => $message_id,
            'text' => "$payed_text",
            'parse_mode' => 'html',
            'reply_markup' => json_encode(['inline_keyboard' => $buttons])
        ]);
    }
    
    if($data == "KM_TRID_AN_TSH7n"){
        bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "- دەتەوێت بڕی چەند $a3ml بکڕیی ؟ :",
        'parse_mode' => 'html',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "sh7n"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id,'MAKE_SH7n');
    }
if ($update->message) {
    if($text and $sessions->get('mode_' . $from_id) === 'MAKE_SH7n'){
        $NOW_s3r = $bot->get("s3r_njom") ?? "1";
        $pricePerThousand = $NOW_s3r; 
    $value = ($text / 1000) * $pricePerThousand;
        $amount = intval($value);
        $T = Invoice($amount,$text );
        bot('SendMessage', [
        'chat_id' => $chat_id, 
        'text' => "- بۆ تەواوکردنی کڕینی $text $a3ml بە $amount ئەستێرە لە ڕێگەی بەستەری خوارەوە ,",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "تەواوکردنی پارەدان", "url" => "$T"]],
            ]
        ])
    ]);
    $sessions->delete('mode_'.$from_id,);
    }

if (isset($update->message->successful_payment)) {
    $STARs = $update->message->successful_payment->total_amount;
    $charge_id = $update->message->successful_payment->telegram_payment_charge_id;
    $NOW_s3r = $bot->get("s3r_njom") ?? "1"; 
    $pricePerThousand = $NOW_s3r;

    $amount = floatval($STARs); 
    $points = intval(($amount / $pricePerThousand) * 1000);

    bot('SendMessage', [
        'chat_id' => $chat_id, 
        'text' => "*- بڕی $STARs ئەستێرەمان لێت وەرگرت ,*\n- بڕی $points $a3ml زیادکرا",
        'parse_mode' => 'Markdown',
    ]);

    $wallets->set('coins_' . $chat_id , $wallets->get('coins_' . $chat_id) + $points);

    bot('SendMessage', [
        'chat_id' => $ADMIN, 
        'text' => "*وەسڵی کڕین ئەستێرە ⭐*

*کڕیار*: [$name](tg://user?id=$from_id)
*ئایدی:* `$from_id`
*بڕی پارەدان:* $STARs
*خاڵی زیادکراو:* $points
*ژمارەی وەسڵ:* `$charge_id`
",
        'parse_mode' => 'Markdown',
    ]);
}
}

if($data == "BUY_WITH_FASTPAY"){
    if(!$bot->get("s3r_fastpay") or !$bot->get("fastpay_number")){
         bot('answerCallbackQuery',[
            'callback_query_id' => $update->callback_query->id,
            'text' => "⚠️ خزمەتگوزاری بەردەست نییە",
            'show_alert' => true,
        ]);
        return;
    }
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "- دەتەوێت بڕی چەند $a3ml بکڕیی ؟ :",
        'parse_mode' => 'html',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "CANCEL_FP_PROCESS"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id,'REQ_FASTPAY_POINTS');
    return;
}


if($data == "CANCEL_FP_PROCESS"){
    $sessions->delete('mode_'.$from_id);
    $sessions->delete('fp_points_'.$from_id);
    $payed_text = $bot->get('payed') ?? "دیاری نەکراوە";
    $agents = $bot->get("agents") ?? [];
    $buttons = [];
    
    foreach ($agents as $agent) {
        if(preg_match('/https/',$agent["link"])){
            $buttons[] = [["text" => $agent["name"], "url" => $agent["link"]]];
        }
    }
        $payment_methods = [];
        if($bot->get('AL_NJOM_x') == '✅'){
            $payment_methods [] = ["text" => "ئەستێرە ⭐", "callback_data" => "KM_TRID_AN_TSH7n"];
        }
        if($bot->get('AL_FASTPAY_x') == '✅'){
            $payment_methods [] = ["text" => "فاستپەی ⚡", "callback_data" => "BUY_WITH_FASTPAY"];
        }
        if($bot->get('AL_FIB_x') == '✅'){
            $payment_methods [] = ["text" => "ئیف ئای بێ 🏦", "callback_data" => "BUY_WITH_FIB"];
        }
        if($bot->get('AL_ASIACELL_x') == '✅'){
            $payment_methods [] = ["text" => "ئاسیاسێڵ 📞", "callback_data" => "BUY_WITH_ASIACELL"];
        }
        $rows = array_chunk($payment_methods, 2);

    foreach($rows as $row){
        $buttons[] = $row;
    }
    $buttons[] = [["text" => "🔙 گەڕانەوە", "callback_data" => "BACK"]];

    bot('EditMessageText', [
            'chat_id' => $chat_id, 
            'message_id' => $message_id,
            'text' => "$payed_text",
            'parse_mode' => 'html',
            'reply_markup' => json_encode(['inline_keyboard' => $buttons])
        ]);
}

if($text and $sessions->get('mode_' . $from_id) === 'REQ_FASTPAY_POINTS'){
    if(!is_numeric($text) || $text < 500){
         bot('SendMessage', [
            'chat_id' => $chat_id, 
            'text' => "❗️ تکایە ژمارەیەکی دروست بنێرە کەمتر نەبێت لە 500",
            'parse_mode' => 'Markdown'
        ]);
        return;
    }
    
    $price_per_1k = $bot->get("s3r_fastpay");
    $total_price = ($text / 1000) * $price_per_1k;
    
    bot('SendMessage', [
        'chat_id' => $chat_id, 
        'text' => "💳 *زانیاری پارەدان (فاستپەی)*\n\n".
                  "💰 بڕی $a3ml: `$text`\n".
                  "💵 بڕی پارە: `$total_price` IQD\n\n".
                  "📞 تکایە ئەم بڕە پارەیە بنێرە بۆ ئەم ژمارەیە:\n".
                  "`" . $bot->get("fastpay_number") . "`\n\n".
                  "📸 *دوای ناردن، وێنەی وەسڵەکە (Screenshot) لێرە بنێرە:*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "CANCEL_FP_PROCESS"]],
            ]
        ])
    ]);
    
    $sessions->set('mode_'.$from_id, 'WAIT_FASTPAY_PROOF');
    $sessions->set('fp_points_'.$from_id, $text);
    return;
}


if($sessions->get('mode_' . $from_id) === 'WAIT_FASTPAY_PROOF'){
    if($update->message->photo){
        $photo_id = end($update->message->photo)->file_id;
        $points = $sessions->get('fp_points_'.$from_id);
        $msg_id_user = $message_id;
        
        $caption = "داواکاری کڕین (فاستپەی) 🧾\n\n".
                   "👤 کڕیار: [$name](tg://user?id=$from_id) .\n".
                   "🆔 ئایدی: `$from_id`\n".
                   "📦 بڕی $a3ml: $points";
                   
        bot('sendPhoto', [
            'chat_id' => $ADMIN,
            'photo' => $photo_id,
            'caption' => $caption,
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [
                        ['text' => "قبوڵکردن ✅", 'callback_data' => "ACC_FP_{$from_id}_{$points}_{$msg_id_user}"],
                        ['text' => "ڕەتکردنەوە ❌", 'callback_data' => "REJ_FP_{$from_id}_{$msg_id_user}"]
                    ]
                ]
            ])
        ]);
        
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*✅ وەسڵەکەت نێردرا بۆ ئەدمین، دوای پێداچوونەوە $a3ml زیاد دەکرێن*",
            'parse_mode' => 'Markdown'
        ]);
        
        $sessions->delete('mode_'.$from_id);
        $sessions->delete('fp_points_'.$from_id);

    } elseif($text) {
        if($text == "/start"){
             $sessions->delete('mode_'.$from_id);
             $sessions->delete('fp_points_'.$from_id);
        } else {
            bot('SendMessage', [
                'chat_id' => $chat_id,
                'text' => "*⚠️ تکایە تەنها وێنەی وەسڵەکە بنێرە*
- نووسین و ژمارە قبوڵ ناکرێت.",
                'parse_mode' => 'Markdown'
            ]);
        }
    }
}
if(preg_match('/^ACC_FP_(.*?)_(.*?)_(.*?)$/', $data, $matches)){
    $uid = $matches[1];
    $pts = $matches[2];
    $mid = $matches[3];
    $wallets->set('coins_'.$uid, $wallets->get('coins_'.$uid) + $pts);
    bot('SendMessage', [
        'chat_id' => $uid,
        'reply_to_message_id' => $mid,
        'text' => "✅ *پیرۆزە! داواکاری کڕینی $a3ml قبوڵ کرا (فاستپەی).*\nبڕی $pts $a3ml زیادکرا بۆ باڵانسەکەت.",
        'parse_mode' => 'Markdown'
    ]);
    bot('editMessageCaption', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'caption' => $update->callback_query->message->caption . "\n\n✅ *قبوڵکرا لەلایەن:* [$name](tg://user?id=$from_id)",
        'parse_mode' => 'Markdown'
    ]);
    bot('answerCallbackQuery', ['callback_query_id' => $update->callback_query->id, 'text' => "داواکارییەکە قبوڵ کرا ✅"]);
}

if(preg_match('/^REJ_FP_(.*?)_(.*?)$/', $data, $matches)){
    $uid = $matches[1];
    $mid = $matches[2];
    bot('SendMessage', [
        'chat_id' => $uid,
        'reply_to_message_id' => $mid,
        'text' => "❌ *داواکاری کڕینی $a3ml ڕەتکرایەوە (فاستپەی)*",
        'parse_mode' => 'Markdown'
    ]);
    bot('editMessageCaption', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'caption' => $update->callback_query->message->caption . "\n\n❌ *ڕەتکرایەوە لەلایەن:* [$name](tg://user?id=$from_id)",
        'parse_mode' => 'Markdown'
    ]);
    bot('answerCallbackQuery', ['callback_query_id' => $update->callback_query->id, 'text' => "داواکارییەکە ڕەتکرایەوە ❌"]);
}


if($data == "BUY_WITH_FIB"){
    if(!$bot->get("s3r_fib") or !$bot->get("fib_number")){
         bot('answerCallbackQuery',[
            'callback_query_id' => $update->callback_query->id,
            'text' => "⚠️ خزمەتگوزاری بەردەست نییە",
            'show_alert' => true,
        ]);
        return;
    }
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "- دەتەوێت بڕی چەند $a3ml بکڕیی ؟ :",
        'parse_mode' => 'html',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "CANCEL_FIB_PROCESS"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id,'REQ_FIB_POINTS');
    return;
}

if($data == "CANCEL_FIB_PROCESS"){
    $sessions->delete('mode_'.$from_id);
    $sessions->delete('fib_points_'.$from_id);
    $payed_text = $bot->get('payed') ?? "دیاری نەکراوە";
    $agents = $bot->get("agents") ?? [];
    $buttons = [];
    
    foreach ($agents as $agent) {
        if(preg_match('/https/',$agent["link"])){
            $buttons[] = [["text" => $agent["name"], "url" => $agent["link"]]];
        }
    }
        $payment_methods = [];
        if($bot->get('AL_NJOM_x') == '✅'){
            $payment_methods [] = ["text" => "ئەستێرە ⭐", "callback_data" => "KM_TRID_AN_TSH7n"];
        }
        if($bot->get('AL_FASTPAY_x') == '✅'){
            $payment_methods [] = ["text" => "فاستپەی ⚡", "callback_data" => "BUY_WITH_FASTPAY"];
        }
        if($bot->get('AL_FIB_x') == '✅'){
            $payment_methods [] = ["text" => "ئیف ئای بێ 🏦", "callback_data" => "BUY_WITH_FIB"];
        }
        if($bot->get('AL_ASIACELL_x') == '✅'){
            $payment_methods [] = ["text" => "ئاسیاسێڵ 📞", "callback_data" => "BUY_WITH_ASIACELL"];
        }
        $rows = array_chunk($payment_methods, 2);

    foreach($rows as $row){
        $buttons[] = $row;
    }
    $buttons[] = [["text" => "🔙 گەڕانەوە", "callback_data" => "BACK"]];

    bot('EditMessageText', [
            'chat_id' => $chat_id, 
            'message_id' => $message_id,
            'text' => "$payed_text",
            'parse_mode' => 'html',
            'reply_markup' => json_encode(['inline_keyboard' => $buttons])
        ]);
}

if($text and $sessions->get('mode_' . $from_id) === 'REQ_FIB_POINTS'){
    if(!is_numeric($text) || $text < 500){
         bot('SendMessage', [
            'chat_id' => $chat_id, 
            'text' => "❗️ تکایە ژمارەیەکی دروست بنێرە کەمتر نەبێت لە 500",
            'parse_mode' => 'Markdown'
        ]);
        return;
    }
    
    $price_per_1k = $bot->get("s3r_fib");
    $total_price = ($text / 1000) * $price_per_1k;
    
    bot('SendMessage', [
        'chat_id' => $chat_id, 
        'text' => "💳 *زانیاری پارەدان (ئیف ئای بێ)*\n\n".
                  "💰 بڕی $a3ml: `$text`\n".
                  "💵 بڕی پارە: `$total_price` IQD\n\n".
                  "📞 تکایە ئەم بڕە پارەیە بنێرە بۆ ئەم ژمارەیە:\n".
                  "`" . $bot->get("fib_number") . "`\n\n".
                  "📸 *دوای ناردن، وێنەی وەسڵەکە (Screenshot) لێرە بنێرە:*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "CANCEL_FIB_PROCESS"]],
            ]
        ])
    ]);
    
    $sessions->set('mode_'.$from_id, 'WAIT_FIB_PROOF');
    $sessions->set('fib_points_'.$from_id, $text);
    return;
}

if($sessions->get('mode_' . $from_id) === 'WAIT_FIB_PROOF'){
    if($update->message->photo){
        $photo_id = end($update->message->photo)->file_id;
        $points = $sessions->get('fib_points_'.$from_id);
        $msg_id_user = $message_id;
        
        $caption = "داواکاری کڕین (ئیف ئای بێ) 🧾\n\n".
                   "👤 کڕیار: [$name](tg://user?id=$from_id) .\n".
                   "🆔 ئایدی: `$from_id`\n".
                   "📦 بڕی $a3ml: $points";
                   
        bot('sendPhoto', [
            'chat_id' => $ADMIN,
            'photo' => $photo_id,
            'caption' => $caption,
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [
                        ['text' => "قبوڵکردن ✅", 'callback_data' => "ACC_FIB_{$from_id}_{$points}_{$msg_id_user}"],
                        ['text' => "ڕەتکردنەوە ❌", 'callback_data' => "REJ_FIB_{$from_id}_{$msg_id_user}"]
                    ]
                ]
            ])
        ]);
        
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*✅ وەسڵەکەت نێردرا بۆ ئەدمین، دوای پێداچوونەوە $a3ml زیاد دەکرێن*",
            'parse_mode' => 'Markdown'
        ]);
        
        $sessions->delete('mode_'.$from_id);
        $sessions->delete('fib_points_'.$from_id);

    } elseif($text) {
        if($text == "/start"){
             $sessions->delete('mode_'.$from_id);
             $sessions->delete('fib_points_'.$from_id);
        } else {
            bot('SendMessage', [
                'chat_id' => $chat_id,
                'text' => "*⚠️ تکایە تەنها وێنەی وەسڵەکە بنێرە*
- نووسین و ژمارە قبوڵ ناکرێت.",
                'parse_mode' => 'Markdown'
            ]);
        }
    }
}

if(preg_match('/^ACC_FIB_(.*?)_(.*?)_(.*?)$/', $data, $matches)){
    $uid = $matches[1];
    $pts = $matches[2];
    $mid = $matches[3];
    $wallets->set('coins_'.$uid, $wallets->get('coins_'.$uid) + $pts);
    bot('SendMessage', [
        'chat_id' => $uid,
        'reply_to_message_id' => $mid,
        'text' => "✅ *پیرۆزە! داواکاری کڕینی $a3ml قبوڵ کرا (ئیف ئای بێ).*\nبڕی $pts $a3ml زیادکرا بۆ باڵانسەکەت.",
        'parse_mode' => 'Markdown'
    ]);
    bot('editMessageCaption', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'caption' => $update->callback_query->message->caption . "\n\n✅ *قبوڵکرا لەلایەن:* [$name](tg://user?id=$from_id)",
        'parse_mode' => 'Markdown'
    ]);
    bot('answerCallbackQuery', ['callback_query_id' => $update->callback_query->id, 'text' => "داواکارییەکە قبوڵ کرا ✅"]);
}

if(preg_match('/^REJ_FIB_(.*?)_(.*?)$/', $data, $matches)){
    $uid = $matches[1];
    $mid = $matches[2];
    bot('SendMessage', [
        'chat_id' => $uid,
        'reply_to_message_id' => $mid,
        'text' => "❌ *داواکاری کڕینی $a3ml ڕەتکرایەوە (ئیف ئای بێ)*",
        'parse_mode' => 'Markdown'
    ]);
    bot('editMessageCaption', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'caption' => $update->callback_query->message->caption . "\n\n❌ *ڕەتکرایەوە لەلایەن:* [$name](tg://user?id=$from_id)",
        'parse_mode' => 'Markdown'
    ]);
    bot('answerCallbackQuery', ['callback_query_id' => $update->callback_query->id, 'text' => "داواکارییەکە ڕەتکرایەوە ❌"]);
}

if($data == "BUY_WITH_ASIACELL"){
    if(!$bot->get("s3r_asiacell") or !$bot->get("asiacell_number")){
         bot('answerCallbackQuery',[
            'callback_query_id' => $update->callback_query->id,
            'text' => "⚠️ خزمەتگوزاری بەردەست نییە",
            'show_alert' => true,
        ]);
        return;
    }
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "- دەتەوێت بڕی چەند $a3ml بکڕیی ؟ :",
        'parse_mode' => 'html',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "CANCEL_ASIACELL_PROCESS"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id,'REQ_ASIACELL_POINTS');
    return;
}

if($data == "CANCEL_ASIACELL_PROCESS"){
    $sessions->delete('mode_'.$from_id);
    $sessions->delete('asia_points_'.$from_id);
    $payed_text = $bot->get('payed') ?? "دیاری نەکراوە";
    $agents = $bot->get("agents") ?? [];
    $buttons = [];
    
    foreach ($agents as $agent) {
        if(preg_match('/https/',$agent["link"])){
            $buttons[] = [["text" => $agent["name"], "url" => $agent["link"]]];
        }
    }
        $payment_methods = [];
        if($bot->get('AL_NJOM_x') == '✅'){
            $payment_methods [] = ["text" => "ئەستێرە ⭐", "callback_data" => "KM_TRID_AN_TSH7n"];
        }
        if($bot->get('AL_FASTPAY_x') == '✅'){
            $payment_methods [] = ["text" => "فاستپەی ⚡", "callback_data" => "BUY_WITH_FASTPAY"];
        }
        if($bot->get('AL_FIB_x') == '✅'){
            $payment_methods [] = ["text" => "ئیف ئای بێ 🏦", "callback_data" => "BUY_WITH_FIB"];
        }
        if($bot->get('AL_ASIACELL_x') == '✅'){
            $payment_methods [] = ["text" => "ئاسیاسێڵ 📞", "callback_data" => "BUY_WITH_ASIACELL"];
        }
        $rows = array_chunk($payment_methods, 2);

    foreach($rows as $row){
        $buttons[] = $row;
    }
    $buttons[] = [["text" => "🔙 گەڕانەوە", "callback_data" => "BACK"]];

    bot('EditMessageText', [
            'chat_id' => $chat_id, 
            'message_id' => $message_id,
            'text' => "$payed_text",
            'parse_mode' => 'html',
            'reply_markup' => json_encode(['inline_keyboard' => $buttons])
        ]);
}

if($text and $sessions->get('mode_' . $from_id) === 'REQ_ASIACELL_POINTS'){
    if(!is_numeric($text) || $text < 1000){
         bot('SendMessage', [
            'chat_id' => $chat_id, 
            'text' => "❗️ تکایە ژمارەیەکی دروست بنێرە کەمتر نەبێت لە 1000",
            'parse_mode' => 'Markdown'
        ]);
        return;
    }
    
    $price_per_1k = $bot->get("s3r_asiacell");
    $total_price = ($text / 1000) * $price_per_1k;
    
    bot('SendMessage', [
        'chat_id' => $chat_id, 
        'text' => "💳 *زانیاری پارەدان (ئاسیاسێڵ)*\n\n".
                  "💰 بڕی $a3ml: `$text`\n".
                  "💵 بڕی پارە: `$total_price` IQD\n\n".
                  "📞 تکایە ئەم بڕە پارەیە بنێرە بۆ ئەم ژمارەیە:\n".
                  "`" . $bot->get("asiacell_number") . "`\n\n".
                  "📱 *دوای ناردن، تکایە تەنها ئەو ژمارە مۆبایلە بنێرە کە باڵانسەکەت پێ ناردووە (بە ژمارەی ئینگلیزی):*\n_نموونە: 0770xxxxxxx_",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "CANCEL_ASIACELL_PROCESS"]],
            ]
        ])
    ]);
    
    $sessions->set('mode_'.$from_id, 'WAIT_ASIACELL_PROOF');
    $sessions->set('asia_points_'.$from_id, $text);
    return;
}

if($sessions->get('mode_' . $from_id) === 'WAIT_ASIACELL_PROOF'){
    if($update->message->photo){
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "❌ *وێنە قبوڵ ناکرێت!*\nتکایە تەنها ژمارەی مۆبایلەکە بنێرە (وەک دەق).",
            'parse_mode' => 'Markdown'
        ]);
        return; 
    }

    if($text){
        if($text == "/start"){
             $sessions->delete('mode_'.$from_id);
             $sessions->delete('asia_points_'.$from_id);
             return;
        }

        if(!is_numeric($text) || strlen($text) < 11){
            bot('SendMessage', [
                'chat_id' => $chat_id,
                'text' => "❌ *تکایە تەنها ژمارەیەکی دروست بنێرە!*\n- نابێت نووسینی تێدابێت.\n- دەبێت ژمارەی مۆبایل بێت (بە ژمارەی ئینگلیزی).",
                'parse_mode' => 'Markdown'
            ]);
            return;
        }

        $points = $sessions->get('asia_points_'.$from_id);
        $msg_id_user = $message_id;
        $phoneNumber = $text;

        $caption = "داواکاری کڕین (ئاسیاسێڵ - ژمارە) 📱\n\n".
                   "👤 کڕیار: [$name](tg://user?id=$from_id) .\n".
                   "🆔 ئایدی: `$from_id`\n".
                   "📦 بڕی $a3ml: `$points`\n".
                   "📞 ژمارەی نێرەر: `$phoneNumber`"; 
        bot('sendMessage', [
            'chat_id' => $ADMIN,
            'text' => $caption,
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [
                        ['text' => "قبوڵکردن ✅", 'callback_data' => "ACC_ASIA_{$from_id}_{$points}_{$msg_id_user}"],
                        ['text' => "ڕەتکردنەوە ❌", 'callback_data' => "REJ_ASIA_{$from_id}_{$msg_id_user}"]
                    ]
                ]
            ])
        ]);
        
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*✅ ژمارەکەت نێردرا بۆ ئەدمین، دوای پێداچوونەوە $a3ml زیاد دەکرێن*",
            'parse_mode' => 'Markdown'
        ]);
        
        $sessions->delete('mode_'.$from_id);
        $sessions->delete('asia_points_'.$from_id);
    }
}


if(preg_match('/^ACC_ASIA_(.*?)_(.*?)_(.*?)$/', $data, $matches)){
    $uid = $matches[1];
    $pts = $matches[2];
    $mid = $matches[3];
    $wallets->set('coins_'.$uid, $wallets->get('coins_'.$uid) + $pts);
    bot('SendMessage', [
        'chat_id' => $uid,
        'reply_to_message_id' => $mid,
        'text' => "✅ *پیرۆزە! داواکاری کڕینی $a3ml قبوڵ کرا (ئاسیاسێڵ).*\nبڕی $pts $a3ml زیادکرا بۆ باڵانسەکەت.",
        'parse_mode' => 'Markdown'
    ]);
    bot('editMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => $update->callback_query->message->text . "\n\n✅ *قبوڵکرا لەلایەن:* [$name](tg://user?id=$from_id)",
        'parse_mode' => 'Markdown'
    ]);
    bot('answerCallbackQuery', ['callback_query_id' => $update->callback_query->id, 'text' => "داواکارییەکە قبوڵ کرا ✅"]);
}

if(preg_match('/^REJ_ASIA_(.*?)_(.*?)$/', $data, $matches)){
    $uid = $matches[1];
    $mid = $matches[2];
    bot('SendMessage', [
        'chat_id' => $uid,
        'reply_to_message_id' => $mid,
        'text' => "❌ *داواکاری کڕینی $a3ml ڕەتکرایەوە (ئاسیاسێڵ)*",
        'parse_mode' => 'Markdown'
    ]);
    bot('editMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => $update->callback_query->message->text . "\n\n❌ *ڕەتکرایەوە لەلایەن:* [$name](tg://user?id=$from_id)",
        'parse_mode' => 'Markdown'
    ]);
    bot('answerCallbackQuery', ['callback_query_id' => $update->callback_query->id, 'text' => "داواکارییەکە ڕەتکرایەوە ❌"]);
}


if($data == 'aggrement'){
    $policy_text = $bot->get('policy') ?? "نییە";
bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "$policy_text",
        'parse_mode' => 'html',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACK"]],
            ]
        ])
    ]);
}

if ($data == 'SERVICES') {
    $qsms_list = explode("\n", $bot->get('qsms'));
    $S_LIST = ['inline_keyboard' => []];
    $buttons = [];
    $added = [];
    $first_added = false;
    $has_active_sections = false; 

    foreach ($qsms_list as $qsms) {
        $qsms = trim($qsms);
        if (empty($qsms) || isset($added[$qsms])) continue;

        $idx = $bot->get('qsms_id_' . $qsms);
        if (empty($idx)) continue;
        
        if ($bot->get('qsm_status_' . $idx) === '❌') {
            continue;
        }
        
        $has_active_sections = true;

        if (!$first_added) {
            $S_LIST['inline_keyboard'][] = [[
                'text' => $qsms,
                'callback_data' => "VIEWQSM_$idx"
            ]];
            $added[$qsms] = true;
            $first_added = true;
            continue;
        }

        $buttons[] = [
            'text' => $qsms,
            'callback_data' => "VIEWQSM_$idx"
        ];
        $added[$qsms] = true;
    }

    foreach (array_chunk($buttons, 2) as $row) {
        $S_LIST['inline_keyboard'][] = $row;
    }

    $S_LIST['inline_keyboard'][] = [['text' => "🔙 گەڕانەوە", 'callback_data' => "BACK"]];

    if ($has_active_sections) {
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'text' => "<b> - لیستی بەشەکان دانەیەک هەڵبژێرە <tg-emoji emoji-id='5431736674147114227'>🗂️</tg-emoji></b>",
            'parse_mode' => 'html',
            'reply_markup' => json_encode($S_LIST)
        ]);
    } else {
        bot('EditMessageText', [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'text' => "*- لە ئێستادا هیچ خزمەتگوزارییەک بەردەست نییە ❎*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "🔙 گەڕانەوە", "callback_data" => "BACK"]],
                ]
            ])
        ]);
    }    
}

$VIEWQSM_ = explode("VIEWQSM_", $data)[1];
if ($VIEWQSM_) {
    //$name_qsm = $bot->get('qsms_name_' . $VIEWQSM_);
    $sessions->delete('mode_' . $from_id);
    $sessions->delete('help_' . $from_id);
    $S_LIST = ['inline_keyboard' => []];
    $buttons = [];
    foreach (explode("\n", $bot->get('xdmat_' . $VIEWQSM_ )) as $xdmats) {
        $idx = $bot->get('xdmat_' . $xdmats);
        if (!empty($xdmats) and !empty($idx)) {
            $buttons[] = ['text' => "$xdmats", 'callback_data' => "TOXDMA_$idx"];
        }
    }

    if(count($buttons) > 0){
        $TXT_MSG = "<b> - ئەوەی دەتەوێت لە خوارەوە هەڵبژێرە <tg-emoji emoji-id='5431499171045581032'>🛒</tg-emoji></b>";
        
        if ($bot->get('style_qsm_' .$VIEWQSM_) == 'ئاسۆیی') {
            $button_rows = array_chunk($buttons, 2);
            foreach ($button_rows as $row) {
                $S_LIST['inline_keyboard'][] = $row;
            }
        } else {
           foreach ($buttons as $btn) {
                $S_LIST['inline_keyboard'][] = [$btn];
            }
        }
    } else {
        $TXT_MSG = "<b> - ببورە لەم بەشە هیچ خزمەتگوزارییەک بەردەست نییە <tg-emoji emoji-id='5467890025217661107'>‼️</tg-emoji></b>";
    }

    $S_LIST['inline_keyboard'][] = [["text" => "🔙 گەڕانەوە", "callback_data" => "SERVICES"]];

    bot('EditMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "$TXT_MSG",
        'parse_mode' => 'html',
        'reply_markup' => json_encode($S_LIST)
    ]);
}
$TOXDMA_ = explode("TOXDMA_",$data)[1];
if($TOXDMA_){
    $ID_XDMA = $TOXDMA_;
    $CHECK = $bot->get('service_status_' . $ID_XDMA);
    if($CHECK == '❌'){
        bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "⚠️ ببورە ئازیزم، ئەم خزمەتگوزارییە لە ئێستادا ڕاگیراوە و کار ناکات!",
        'show_alert' => true,
    ]);
    return;
    }
 $DOMIN = $bot->get('XDMA_INF_DOMIN__'. $ID_XDMA) ?? "دانەنراوە";
    $API = $bot->get('XDMA_INF_KEY__'. $ID_XDMA) ?? "دانەنراوە";
    $MIN = $bot->get('XDMA_INF_MIN__'. $ID_XDMA) ?? "دانەنراوە";
    $MAX = $bot->get('XDMA_INF_MAX__'. $ID_XDMA) ?? "دانەنراوە";
    $PRICE = $bot->get('XDMA_INF_PRICE__'. $ID_XDMA) ?? "دانەنراوە";
    $ID = $bot->get('XDMA_INF_ID__'. $ID_XDMA) ?? "دانەنراوە";
    $description  = $bot->get('XDMA_INF_DESCRIPTION__'. $ID_XDMA) ?? "• بەستەر بنێرە بۆ تەواوکردنی داواکاری:";
    if($bot->get('XDMA_INF_TSLEM__'. $ID_XDMA) == 'دەستی'){
        $ID = 3;
    }
    if(is_numeric($ID)){
    $price = $PRICE * 1000;

    $qsm_id= $bot->get('xdmatinqsm_'. $TOXDMA_);
    $qsm_name = $bot->get('qsms_name_' . $qsm_id);
    $name_xdma = $bot->get('xdmatname_'.$TOXDMA_);
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "🛍 *دروستکردنی داواکاری نوێ*

💎 *خزمەتگوزاری:* $name_xdma
💰 *نرخ:* $price $a3ml (بۆ هەر 1k)
📉 *کەمترین بڕ:* $MIN
📈 *زۆرترین بڕ:* $MAX

🔢 *تکایە ژمارەی ئەو بڕەی دەتەوێت بنێرە:* 👇",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "VIEWQSM_$qsm_id"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id,'MAKE_TLB');
    $sessions->set('xdma_'.$from_id,$TOXDMA_);

}else{
    bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "ئەم خزمەتگوزارییە لە ئێستادا کار ناکات و لەژێر چاکسازی دایە ✅",
        'show_alert' => true,
    ]);
}
return;
}
if (!empty($text) && $sessions->get('mode_' . $from_id) === 'MAKE_TLB') {
    $coins = (int) ($wallets->get('coins_' . $chat_id) ?? 0);
    $xdma_id = $sessions->get('xdma_' . $from_id);
    $ID_XDMA = $xdma_id;
    $DOMIN = $bot->get('XDMA_INF_DOMIN__'. $ID_XDMA) ?? "دانەنراوە";
    $API = $bot->get('XDMA_INF_KEY__'. $ID_XDMA) ?? "دانەنراوە";
    $MIN = $bot->get('XDMA_INF_MIN__'. $ID_XDMA) ?? "دانەنراوە";
    $MAX = $bot->get('XDMA_INF_MAX__'. $ID_XDMA) ?? "دانەنراوە";
    $PRICE = $bot->get('XDMA_INF_PRICE__'. $ID_XDMA) ?? "دانەنراوە";
    $ID = $bot->get('XDMA_INF_ID__'. $ID_XDMA) ?? "دانەنراوە";
    $description  = $bot->get('XDMA_INF_DESCRIPTION__'. $ID_XDMA) ?? "• بەستەر بنێرە بۆ تەواوکردنی داواکاری:";

    
    $amount = (int) $text;
    $price = $PRICE * $amount;
    
    if ($amount <= 0) {
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "تکایە تەنها ژمارە بنێرە ❗️",
            'parse_mode' => 'Markdown',
        ]);
        return;
    }
    
    if ($coins < $price) {
        $need = $price - $coins;
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*$a3ml ت بەش ناکات بۆ تەواوکردنی داواکاری ❎*\n- نرخ : *$price* $a3ml\n- پێویستت بە : *$need* $a3ml هەیە",
            'parse_mode' => 'Markdown',
        ]);
        return;
    }
    
    if ($amount < $MIN || $amount > $MAX) {
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*تکایە ژمارەیەک بنێرە لە نێوان $MIN و $MAX 🔣*",
            'parse_mode' => 'Markdown',
        ]);
        return;
    }
    
    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => "*داوای $amount دەکەیت بە بەهای $price $a3ml ✅*\n$description",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [['text' => "هەڵوەشاندنەوە ❌", 'callback_data' => "cancel"]],
            ]
        ]),
    ]);
    
    $sessions->set('count_' . $from_id, $amount);
    $sessions->set('mode_' . $from_id, 'MAKE_ORDER');
    return;
}

if (!empty($text) && $sessions->get('mode_' . $from_id) === 'MAKE_ORDER') {
    $count = (int) ($sessions->get('count_' . $from_id) ?? 0);
    $coins = (int) ($wallets->get('coins_' . $chat_id) ?? 0);
    $xdma_id = $sessions->get('xdma_' . $from_id);
     $ID_XDMA = $xdma_id;
 $DOMIN = $bot->get('XDMA_INF_DOMIN__'. $ID_XDMA) ?? "دانەنراوە";
    $API = $bot->get('XDMA_INF_KEY__'. $ID_XDMA) ?? "دانەنراوە";
    $MIN = $bot->get('XDMA_INF_MIN__'. $ID_XDMA) ?? "دانەنراوە";
    $MAX = $bot->get('XDMA_INF_MAX__'. $ID_XDMA) ?? "دانەنراوە";
    $PRICE = $bot->get('XDMA_INF_PRICE__'. $ID_XDMA) ?? "دانەنراوە";
    $ID = $bot->get('XDMA_INF_ID__'. $ID_XDMA) ?? "دانەنراوە";
    $description  = $bot->get('XDMA_INF_DESCRIPTION__'. $ID_XDMA) ?? "• بەستەر بنێرە بۆ تەواوکردنی داواکاری:";

    

    $price = $count * $PRICE;
    
    if ($coins < $price) {
        $need = $price - $coins;
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*$a3ml ت بەش ناکات بۆ تەواوکردنی داواکاری ❎*\n- نرخ : *$price* $a3ml\n- پێویستت بە : *$need* $a3ml هەیە",
            'parse_mode' => 'Markdown',
        ]);
        return;
    }
    
    $qsm_id = $bot->get('xdmatinqsm_' . $xdma_id);
    $qsm_name = $bot->get('qsms_name_' . $qsm_id);
    $name_xdma = $bot->get('xdmatname_' . $xdma_id);
    
    bot('SendMessage', [
        'chat_id' => $chat_id,
        'text' => "*📄 زانیاری پێش تەواوکردنی داواکاری*

💎 *خزمەتگوزاری :* $name_xdma
📂 *بەش :* $qsm_name
🔗 *بەستەر :* `$text`
🔢 *بڕی داواکراو :* $count
💰 *تێچوو :* $price $a3ml

*⚠️ تکایە پێش تەواوکردن دڵنیابەرەوە لە زانیارییەکان*",
        'parse_mode' => 'Markdown',
        'disable_web_page_preview' => true,
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [['text' => "تەواوکردنی دروستکردنی داواکاری ✅", 'callback_data' => "maketlb"]],
                [['text' => "هەڵوەشاندنەوەی دروستکردنی داواکاری ❌", 'callback_data' => "cancel"]],
            ]
        ]),
    ]);
    
    $sessions->set('link_' . $from_id, $text);
    $sessions->delete('mode_' . $from_id);
    return;
}


if($data == "maketlb"){
    $QSM = $bot->get('xdmatinqsm_'.$sessions->get('xdma_' . $from_id));

    if($bot->get('toggle_24_'.$QSM) == '✅' && $chat_id != ADMIN) {
        if($sessions->get('I_USEQSM_'.$from_id ."_". $QSM)){
            $time = $sessions->get('I_USEQSM_'.$from_id ."_". $QSM);
            $E = time() - $time;
            $timerDuration = 86400;

            if ($E < $timerDuration) {
                $timeLeft = $timerDuration - $E;
                $hours = floor($timeLeft / 3600);
                $minutes = floor(($timeLeft % 3600) / 60);
                $seconds = $timeLeft % 60;
                
                if($hours > 0){
                    $v = "$hours کاتژمێر";
                } elseif($minutes > 0){
                    $v = "$minutes خولەک";
                } else {
                    $v = "$seconds چرکە";
                }

                bot('EditMessageText', [
                    'chat_id' => $chat_id, 
                    'message_id' => $message_id,
                    'text' => "*• دەتوانیت خزمەتگوزارییەکانی ئەم بەشە تەنها 24 کاتژمێر جارێک بەکاربهێنیت ❎*
- دووبارە هەوڵ بدەرەوە دوای $v ✅
",
                    'parse_mode' => 'Markdown',
                    'disable_web_page_preview' => true,
                ]);
                return;
            }
        }
    }

    $count = (int) $sessions->get('count_' . $from_id);
    $coins = (int) ($wallets->get('coins_' . $chat_id) ?? 0);
    $xdma_id = $sessions->get('xdma_' . $from_id);
    $ID_XDMA = $xdma_id;
    $DOMIN = $bot->get('XDMA_INF_DOMIN__'. $ID_XDMA) ?? "دانەنراوە";
    $API = $bot->get('XDMA_INF_KEY__'. $ID_XDMA) ?? "دانەنراوە";
    $MIN = $bot->get('XDMA_INF_MIN__'. $ID_XDMA) ?? "دانەنراوە";
    $MAX = $bot->get('XDMA_INF_MAX__'. $ID_XDMA) ?? "دانەنراوە";
    $PRICE = $bot->get('XDMA_INF_PRICE__'. $ID_XDMA) ?? "دانەنراوە";
    $ID = $bot->get('XDMA_INF_ID__'. $ID_XDMA) ?? "دانەنراوە";
    $description  = $bot->get('XDMA_INF_DESCRIPTION__'. $ID_XDMA) ?? "• بەستەر بنێرە بۆ تەواوکردنی داواکاری:";

    $price = $count * $PRICE;
    if($bot->get("GENERALS_DOMINX_".$sessions->get('xdma_' . $from_id))){
        $DOMIN = $bot->get('GENERALS_DOMIN');
        $API = $bot->get('GENERALS_KEY');
    }

    if($bot->get('XDMATSOTHER_'. $sessions->get('xdma_' . $from_id))){
        $DOMIN = explode('|',$bot->get('XDMATSOTHER_'. $sessions->get('xdma_' . $from_id)))[0];
        $API = explode('|',$bot->get('XDMATSOTHER_'. $sessions->get('xdma_' . $from_id)))[1];
    }
    $TO = $sessions->get('link_'.$from_id);
    if ($coins >= $price && $count > 0) {
        $api_url = "https://$DOMIN/api/v2?key=$API&action=add&service=$ID&quantity=$count&link=" . urlencode($TO);
        $api_content = file_get_contents($api_url);
        $api_response = json_decode($api_content);

        $ORDER = $api_response->order ?? null;
        $ERROR_MSG = $api_response->error ?? "هەڵەیەکی نەزانراو لە پەیوەندی لەگەڵ سێرڤەر";

       $OKXx = false;
       if($bot->get('XDMA_INF_TSLEM__'. $ID_XDMA) == 'دەستی'){
        $OKXx = true;
        $ORDER = rand(15555,355555);
       }
        if($ORDER or $OKXx){
        if ($price > 0) {
            bot('SendMessage', [
                'chat_id' => $chat_id,
                'text' => "*بڕی $price $a3ml لە هەژمارەکەت کەمکرایەوە ✅*",
                'parse_mode' => 'Markdown',
            ]);
           }
            $xdma = $bot->get('xdmatname_'.$sessions->get('xdma_' . $from_id));
    $coinsor = $wallets->get('coins_'.$chat_id) ?? "0";
    $NOW_NQAT = $coinsor - $price;

    $H = bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*✅ داواکارییەکەت بە سەرکەوتوویی وەرگیرا*

🪪 *ژمارەی داواکاری :* `$ORDER`
💎 *خزمەتگوزاری :* $xdma
🔗 *داواکراوە بۆ :* `$TO`
🔢 *بڕ :* $count
💰 *تێچوو :* $price $a3ml
👛 *باڵانسی ماوە :* $NOW_NQAT $a3ml

*🚀 دەستبەجێ دەست دەکرێت بە جێبەجێکردنی*",
        'parse_mode' => 'Markdown',
        'disable_web_page_preview' => true,
    ]);
    $coinsor = $wallets->get('coins_'.$chat_id) ?? "0";
    $coinsleft = $wallets->get('coinsuseed_'.$from_id) ?? "0";
    $hdaiacount = $wallets->get('hdiacoins_'.$from_id) ?? "0";
    $hdiacountx =$wallets->get('hdiax_'.$from_id) ?? "0";
    $transers = $wallets->get('transcoins_'.$from_id) ?? "0";
    $i_trans = $wallets->get('transsucces_'.$from_id)  ?? "0";
    $invits_count = $wallets->get('countshare_'.$from_id) ?? "0";
    $coinsmeshare = $wallets->get('coinsshare_'.$from_id) ?? "0";
    $NOW_NQAT = $coinsor - $price;
    $CH_TLB = $bot->get('chs_tlbat');

    $ii = $bot->get('qsms_name_' . $bot->get('xdmatinqsm_'. $xdma_id));
    $YY = $bot->get('ORDERS') + 1;
    $TH_STAR = str_replace(array('#a','#b' , '#c' , '#d' , '#e' , '#f' , '#g' , '#h' , '#i' , '#j' ,'#k') , array("[$name](tg://user?id=$from_id)" ,"$name" , "$from_id" , "[$username]" ,$wallets->get('coins_'.$chat_id) , $xdma , $ORDER , $YY , $price , $count ,$ii) , $bot->get('rsala_nshr_text'));
   if($bot->get('rsala_nshr_text')){
    $NSHR =  $TH_STAR;
   }else{
    $NSHR = "*✅ داواکاری نوێ*

• *ژمارەی داواکاری:* `$ORDER`
• *خزمەتگوزاری:* $xdma
• *کڕیار* : [$name](tg://user?id=".IDBot.")";
   }
    $YY = bot('SendMessage', [
                'chat_id' => "@" .$CH_TLB,
                'text' => "$NSHR
",
'disable_web_page_preview' => true,
                'parse_mode' => 'Markdown',
                'reply_markup' => json_encode([
            'inline_keyboard' => [
                [['text' => "بۆ چوونە ناو بۆت ⚡️", 'url' => "https://t.me/$usrbot?start=start"]],
            ]
        ]),
            ]);
            $ish3ar_tlbat = $bot->get('shi3ar_tlbat') ?? '✅';
            if($bot->get('XDMA_INF_TSLEM__'. $ID_XDMA) == 'دەستی'){
                $UU = "تەواوکردنی داواکاری ✅";
            }
if($ish3ar_tlbat == '✅'){
    $Y = bot('SendMessage', [
                'chat_id' => $ADMIN,
                'text' => "*✅ داواکارییەکی نوێ لە بۆتەکەت*"."

*📝 زانیاری داواکاری:*
• *ژمارەی داواکاری:* `$ORDER`
• *خزمەتگوزاری:* $xdma
• *داواکراوە بۆ:* `$TO`
• *بڕ:* *$count*
• *تێچوو:* *$price* $a3ml

*👤 زانیاری کەسەکە:*
• *ناو:* [$name](tg://user?id=$from_id)
• *ئایدی:* `$from_id`
• *یوزەر:* [@$user]
• *ژمارەی $a3ml:* $coinsor
• *$a3ml ی بەکارهێنراو:* $coinsleft
• *$a3ml ی دیاری:* $hdaiacount
• *ژمارەی بانگهێشت:* $invits_count
• *$a3ml لە بەستەری بڵاوکردنەوە:* $coinsmeshare

• *بووە خاوەنی ".$a3ml." :* $NOW_NQAT
",
'disable_web_page_preview' => true,
                'parse_mode' => 'Markdown',
                'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "$UU", "callback_data" => "ACCEDK_". $H->result->message_id."_". $from_id]],
            ]
        ])
            ]);
            if($bot->get('XDMA_INF_TSLEM__'. $ID_XDMA) == 'دەستی'){
                bot('SendMessage', [
            'chat_id' => $ADMIN,
            'reply_to_message_id' => $Y->result->message_id,
            'text' => "*ئاگاداری:* ئەم خزمەتگوزارییە دەستییە 
- *پێویستە بە *دەستی* داواکاری کڕیار *تەواو بکەیت* !

*- بەپێی ڕێکخستنەکانت بەڕێز ئەدمین*",
            'parse_mode' => 'Markdown',
        ]);
        
            }
        }
    $ordtext = "• داواکاری : $ORDER ✅
• خزمەتگوزاری : $xdma 🔠";

if($bot->get('toggle_24_'.$QSM) == '✅'){
    $sessions->set('I_USEQSM_'.$from_id ."_". $QSM , time());
}
$orders->set($ORDER,$API ."|".$DOMIN ."|$xdma|$TO|$count|$price|$from_id");
$cache->set('ORDERS',$cache->get('ORDERS') ."\n". $ORDER);
$cache->set('ORDER_'.$ORDER,$from_id);
$cache->set('ORDER_MSG_ID_'.$ORDER,$H->result->message_id);
$cache->set('ORDER_PRICE_'.$ORDER,$price);
$cache->set('ORDER_INFO_'.$ORDER,$API ."|".$DOMIN ."|". $TO ."|". $xdma ."|". time());
    $wallets->set('MYORDERSTEXT_'.$from_id,$wallets->get('MYORDERSTEXT_'.$from_id) ."\n\n". $ordtext);
    $bot->set('ORDERS',$bot->get('ORDERS') + 1);
    $wallets->set('MYORDERS_'.$from_id,$wallets->get('MYORDERS_'.$from_id) + 1);
    $wallets->set('coinsuseed_'.$from_id,$wallets->get('coinsuseed_'.$from_id) + $price);
    $wallets->set('coins_'.$from_id,$wallets->get('coins_'.$from_id) - $price);
    $sessions->delete('mode_'.$from_id);
    $sessions->delete('xdma_'.$from_id);
    $sessions->delete('count_'.$from_id);
    $sessions->delete('link_'.$from_id);
}else{
    $SUPPRT = "tg://user?id=". ADMIN;
    $CHS = $bot->get('chs_bot') ?? "@SARKAUT";
    if($bot->get('chs_support')){
        $SUPPRT = "https://t.me/" . $bot->get('chs_support');
    }
    
    $xdma_name_error = $bot->get('xdmatname_'.$sessions->get('xdma_' . $from_id));

    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*❌ کێشەیەک ڕوویدا لە کاتی ناردنی داواکاری $xdma_name_error*

⚠️ *هۆکاری ڕەتکردنەوە :*`$ERROR_MSG`

❗️ تکایە ئەم پەیامە بنێرە بۆ پشتیوانی بۆ ئەوەی کێشەکە چارەسەر بکەن",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
                    'inline_keyboard' => [
                        [["text" => "👨‍💻 پەیوەندی بە پشتیوانی", "url" => "$SUPPRT"]],
                        [["text" => "📣 کەناڵی بۆت", "url" => "https://t.me/$CHS"]],
                    ]
                ])
    ]);
    $sessions->delete('mode_'.$from_id);
    $sessions->delete('xdma_'.$from_id);
    $sessions->delete('count_'.$from_id);
    $sessions->delete('link_'.$from_id);
}
}else{
    $need = $price - $coins;
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*$a3ml ت بەش ناکات بۆ تەواوکردنی داواکاری ❎*\n- نرخ : *$price* $a3ml\n- پێویستت بە : *$need* $a3ml هەیە",
        'parse_mode' => 'Markdown',
    ]);
}
}

if ($data == 'toggle_notify_funding' || $data == 'toggle_notify_referral') {
    $type = str_replace('toggle_notify_', '', $data);
    $key = 'notify_' . $type . '_' . $from_id;

    $current_status = $wallets->get($key) ?? '✅';
    $new_status = ($current_status == '✅') ? '❌' : '✅';
    $wallets->set($key, $new_status);

    bot('answerCallbackQuery', [
        'callback_query_id' => $update->callback_query->id
    ]);

    $data = 'acount_me'; 
}

if($data == 'acount_me'){
    $notify_funding_status = $wallets->get('notify_funding_' . $from_id) ?? '✅';
    $notify_referral_status = $wallets->get('notify_referral_' . $from_id) ?? '✅';

    $coins = $wallets->get('coins_'.$chat_id) ?? "0";
    $coinsleft = $wallets->get('coinsuseed_'.$from_id) ?? "0";
    $hdaiacount = $wallets->get('hdiacoins_'.$from_id) ?? "0";
    $hdiacountx =$wallets->get('hdiax_'.$from_id) ?? "0";
    $transers = $wallets->get('transcoins_'.$from_id) ?? "0";
    $i_trans = $wallets->get('transsucces_'.$from_id)  ?? "0";
    $invits_count = $wallets->get('countshare_'.$from_id) ?? "0";
    $coinsmeshare = $wallets->get('coinsshare_'.$from_id) ?? "0";

    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*👤 زانیاری هەژمارەکەت*

💰 *باڵانسی بەردەست :* `$coins` $a3ml
💸 *خاڵ خەرجکراو :* `$coinsleft` $a3ml

🎁 *دیارییە وەرگیراوەکان :* `$hdiacountx` دیاری
🧧 *خاڵ لە دیارییەکان :* `$hdaiacount` $a3ml

📤 *خاڵ نێردراو :* `$transers` $a3ml
📥 *خاڵ وەرگیراو :* `$i_trans` $a3ml

👥 *ژمارەی بانگهێشت :* `$invits_count` کەس
🔗 *خاڵ لە بانگهێشت :* `$coinsmeshare` $a3ml
",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [
                    ['text' => $notify_funding_status, 'callback_data' => "toggle_notify_funding"],
                    ['text' => "ئاگاداری ئەندام", 'callback_data' => "info_notify_funding"]
                ],
                [
                    ['text' => $notify_referral_status, 'callback_data' => "toggle_notify_referral"],
                    ['text' => "ئاگاداری بانگهێشت", 'callback_data' => "info_notify_referral"]
                ],
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACK"]],
            ]
        ])
    ]);
}

if ($data == 'info_notify_funding' || $data == 'info_notify_referral') {
    $info_text = "";

    if ($data == 'info_notify_funding') {
        $info_text = "ℹ️ ئاگادارییەکانی ئەندام:\n\n✅ چالاک: پەیامێکت پێدەگات بۆ هەر ئەندامێکی نوێ کە جۆینی کەناڵەکەت دەکات لە ڕێگەی خزمەتگوزاری ئەندام.\n\n❌ ناچالاک: بێزار ناکرێیت بە ئاگاداری جۆینی ئەندامان.";
    } 
    
    if ($data == 'info_notify_referral') {
        $info_text = "ℹ️ ئاگادارییەکانی بانگهێشت:\n\n✅ چالاک: پەیامێکت پێدەگات کاتێک کەسێکی نوێ جۆینی بۆت دەکات بە بەکارهێنانی بەستەری بانگهێشتی تۆ.\n\n❌ ناچالاک: ئاگاداری وەرناگریت دەربارەی بانگهێشتە نوێیەکان.";
    }

    bot('answerCallbackQuery', [
        'callback_query_id' => $update->callback_query->id,
        'text' => $info_text,
        'show_alert' => true
    ]);
    return; 
}

if($data == 'use_code'){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*🎟 تکایە کۆدی دیاری بنێرە:*",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACK"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id, 'use_code');
}

if($text and $sessions->get('mode_'.$from_id) == 'use_code'){
    $sessions->delete('mode_'.$from_id);
    
    if(!$sessions->get('hdia_'.$text)){
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "❌ *کۆدەکە هەڵەیە یان بەسەرچووە!*",
            'parse_mode' => 'Markdown',
        ]);
        return;
    }

    if($cache->get('IM_USE_'.$from_id.'_'.$text)){
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "⚠️ *تۆ پێشتر سوودمەند بوویت لەم کۆدە!*",
            'parse_mode' => 'Markdown',
        ]);
        return;
    }

    $COOIN = $sessions->get('hdia_'.$text);
    $COUNT_HDIA = $sessions->get('hdia_count_'.$text);
    $NOW_COUNT = $sessions->get('hdia_count_now_'.$text) ?? 0;

    if($NOW_COUNT < $COUNT_HDIA){
        $my_rank = $NOW_COUNT + 1;
        $sessions->set('hdia_count_now_'.$text, $my_rank);
        
        $wallets->set('coins_'.$from_id, $wallets->get('coins_'.$from_id) + $COOIN);
        $wallets->set('hdiax_'.$from_id, $wallets->get('hdiax_'.$from_id) + 1);
        $wallets->set('hdiacoins_'.$from_id, $wallets->get('hdiacoins_'.$from_id) + $COOIN);
        $cache->set('IM_USE_'.$from_id.'_'.$text, true);

        if($my_rank == 1){
            $msg_content = "🎉 *پیرۆزە پاڵەوان!* 🥇\n\nتۆ *یەکەم کەس* بوویت ئەم کۆدە بەکاربهێنیت! 🚀\nبڕی *$COOIN* $a3ml ت دەستکەوت.";
        } else {
            $msg_content = "✅ *کۆدەکە بە سەرکەوتوویی بەکارهات!* 🎟\n\nبڕی *$COOIN* $a3ml ت دەستکەوت.\nتۆ کەسی ژمارە *$my_rank* بوویت لە بەکارهێنانی ئەم کۆدە. 👥";
        }

        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => $msg_content,
            'parse_mode' => 'Markdown',
        ]);

        foreach($ADMINS as $ADMIN){
            $TBQA = $COUNT_HDIA - $my_rank;
            bot('SendMessage', [
                'chat_id' => $ADMIN,
                'text' => "*🔔 کەسێک کۆدی دیاری بەکارهێنا 👤*\n\n👤 *ناو:* [$name](tg://user?id=$from_id)\n📇 *ئایدی:* `$from_id`\n💰 *بڕی وەرگیراو:* $COOIN $a3ml\n🎫 *کۆد:* `$text`\n🔢 *ڕیزبەندی:* کەسی $my_rank\n📉 *ژمارەی ماوە:* $TBQA کەس",
                'parse_mode' => 'Markdown',
            ]);
        }

    } else {
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "⚠️ ببورە، ژمارەی دیاری کراو بۆ ئەم کۆدە تەواو بووە.",
            'parse_mode' => 'Markdown',
        ]);
    }
}


if($data == 'transfer_coin'){
    $a3mola = $bot->get('3mola') ?? "15";
    $my_coins = $wallets->get('coins_'.$chat_id) ?? 0;
    
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*🔁 بەشی گواستنەوەی $a3ml*
        
• باڵانسی بەردەست: `$my_coins` $a3ml
• عمولەی گواستنەوە: `$a3mola` $a3ml

تکایە سەرەتا شێوازی گواستنەوەکە دیاری بکە:",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "👤 ناردن لەریگەی ئایدی", "callback_data" => "choose_transfer_id"]],
                [["text" => "🔗 ناردن لەریگەی بەستەر", "callback_data" => "choose_transfer_link"]],
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACK"]],
            ]
        ])
    ]);
    $sessions->delete('mode_'.$from_id);
    $sessions->delete('temp_amount_'.$from_id); 
}

if($data == 'choose_transfer_id'){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*👤 ناردنی $a3ml لەریگەی ئایدی*

تکایە بڕی ئەو خاڵانە بنێرە کە دەتەوێت بیگوێزیتەوە:",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "transfer_coin"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id, 'req_amount_for_id');
}

if($text and $sessions->get('mode_'.$from_id) == 'req_amount_for_id'){
    if(!is_numeric($text) || $text <= 0){
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "تکایە ژمارەیەکی دروست بنێرە (وەک بڕی $a3ml) ❗️",
            'parse_mode' => 'Markdown',
        ]);
        return;
    }

    $amount = intval($text);
    $a3mola = $bot->get('3mola') ?? "15";
    $total_deduction = $amount + $a3mola;
    $my_coins = $wallets->get('coins_'.$chat_id) ?? 0;

    if($my_coins >= $total_deduction){
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "• بڕی گواستنەوە: `$amount` $a3ml
• کۆی گشتی (لەگەڵ عمولە): `$total_deduction` $a3ml

ئێستا ئایدی کەسی وەرگر بنێرە:",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "🔙 گەڕانەوە", "callback_data" => "transfer_coin"]],
                ]
            ])
        ]);

        $sessions->set('mode_'.$from_id, 'req_id_for_transfer');
        $sessions->set('temp_amount_'.$from_id, $amount);
    } else {
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "❌ باڵانست بەش ناکات بۆ ئەم کردارە 
            
• باڵانست: `$my_coins`
• پێویست: `$total_deduction`",
            'parse_mode' => 'Markdown',
        ]);
    }
    return;
}

if($text and $sessions->get('mode_'.$from_id) == 'req_id_for_transfer'){
    $target_id = trim($text);

    if(!is_numeric($target_id)){
         bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "ئایدی هەڵەیە، تکایە تەنها ژمارە بنێرە ⚠️",
            'parse_mode' => 'Markdown',
        ]);
        return;
    }

    $amount = $sessions->get('temp_amount_'.$from_id);
    $a3mola = $bot->get('3mola') ?? "15";
    $total_deduction = $amount + $a3mola;
    
    $my_coins = $wallets->get('coins_'.$chat_id) ?? 0;
    
    if($my_coins < $total_deduction){
        bot('SendMessage', ['chat_id' => $chat_id, 'text' => "باڵانست بەش ناکات.", 'parse_mode' => 'Markdown']);
        $sessions->delete('mode_'.$from_id);
        $sessions->delete('temp_amount_'.$from_id);
        return;
    }

    if($target_id != $from_id){
        if($users->get($target_id)){ 
            
            $wallets->set('coins_'.$from_id, $wallets->get('coins_'.$from_id) - $total_deduction);
            $wallets->set('transcoins_'.$from_id, $wallets->get('transcoins_'.$from_id) + $amount);
            
            $wallets->set('coins_'.$target_id, $wallets->get('coins_'.$target_id) + $amount);
            $wallets->set('transsucces_'.$target_id, $wallets->get('transsucces_'.$target_id) + $amount);

            bot('SendMessage', [
                'chat_id' => $chat_id,
                'text' => "*گواستنەوە سەرکەوتوو بوو ✅*

• بڕی نێردراو: `$amount` $a3ml
• بۆ ئایدی: `$target_id`
• عمولە: `$a3mola` $a3ml",
                'parse_mode' => 'Markdown',
                'reply_markup' => json_encode([
                    'inline_keyboard' => [
                        [["text" => "🔙 گەڕانەوە", "callback_data" => "transfer_coin"]],
                    ]
                ])
            ]);

            bot('SendMessage', [
                'chat_id' => $target_id,
                'text' => "*بڕی $amount $a3ml گوازرایەوە بۆ هەژمارەکەت*
لەلایەن: `$from_id`",
                'parse_mode' => 'Markdown',
            ]);

            $sessions->delete('mode_'.$from_id);
            $sessions->delete('temp_amount_'.$from_id);

        } else {
            bot('SendMessage', [
                'chat_id' => $chat_id,
                'text' => "ئەم ئایدییە (`$target_id`) لەناو بۆت تۆمار نییە ❌",
                'parse_mode' => 'Markdown',
            ]);
        }
    } else {
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "ناتوانیت خاڵ بۆ خۆت بنێریت ❗️",
            'parse_mode' => 'Markdown',
        ]);
    }
}

if($data == 'choose_transfer_link'){
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "*🔗 ناردنی $a3ml لەریگەی بەستەر*

تکایە بڕی ئەو خاڵانە بنێرە کە دەتەوێت بیکەیت بە بەستەر:",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "🔙 گەڕانەوە", "callback_data" => "transfer_coin"]],
            ]
        ])
    ]);
    $sessions->set('mode_'.$from_id, 'req_amount_for_link');
}

if($text and $sessions->get('mode_'.$from_id) == 'req_amount_for_link'){
    if(!is_numeric($text) || $text <= 0){
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "تکایە ژمارەیەکی دروست بنێرە ⚠️",
            'parse_mode' => 'Markdown',
        ]);
        return;
    }

    $amount = intval($text);
    $a3mola = $bot->get('3mola') ?? "15";
    $total_deduction = $amount + $a3mola;
    $my_coins = $wallets->get('coins_'.$chat_id) ?? 0;

    if($my_coins >= $total_deduction){
        
        $get = coderandom(32);
        
        $wallets->set('coins_'.$from_id, $wallets->get('coins_'.$from_id) - $total_deduction);
        $wallets->set('transcoins_'.$from_id, $wallets->get('transcoins_'.$from_id) + $amount);

        $sessions->set('LINK_'.$get, $amount);
        $sessions->set('LINK_OWNER_'.$get, $from_id);
        $sessions->set('LINK_TIME_'.$get, time());

        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "*بەستەری $a3ml دروستکرا ✅*

• بڕی ناو بەستەر: `$amount` $a3ml
• کەمکرایەوە لە باڵانس: `$total_deduction` $a3ml

🔗 بەستەر:
`https://t.me/$USRBOT?start=by$get`",
            'parse_mode' => 'Markdown',
            'disable_web_page_preview' => true,
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "❎ ڕاگرتنی بەستەر", "callback_data" => "stoprabt_$get"]],
                    [["text" => "🔙 گەڕانەوە", "callback_data" => "transfer_coin"]],
                ]
            ])
        ]);
        
        $sessions->delete('mode_'.$from_id);
    } else {
        bot('SendMessage', [
            'chat_id' => $chat_id,
            'text' => "❌ باڵانست بەش ناکات بۆ ئەم کردارە
            
• باڵانست: `$my_coins`
• پێویست: `$total_deduction`",
            'parse_mode' => 'Markdown',
        ]);
    }
}

$stoprabt = explode("stoprabt_", $data)[1];
if($stoprabt){
    if($sessions->get('LINK_'.$stoprabt)){
        $amount = $sessions->get('LINK_'.$stoprabt);
        
        $wallets->set('coins_'.$from_id, $wallets->get('coins_'.$from_id) + $amount);
        
        $sessions->delete('LINK_'.$stoprabt);
        $sessions->delete('LINK_OWNER_'.$stoprabt);
        
        bot('EditMessageText', [
            'chat_id' => $chat_id, 
            'message_id' => $message_id,
            'text' => "*بەستەرەکە هەڵوەشێندرایەوە و بڕی $amount $a3ml گەڕێندرایەوە بۆ باڵانسەکەت ✅*",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [["text" => "🔙 گەڕانەوە", "callback_data" => "transfer_coin"]],
                ]
            ])
        ]);
    } else {
        bot('answerCallbackQuery', [
            'callback_query_id' => $update->callback_query->id,
            'text' => "ئەم بەستەرە پێشتر بەکارهاتووە یان سڕدراوەتەوە ❗️",
            'show_alert' => true,
        ]);
        bot('EditMessageText', [
            'chat_id' => $chat_id, 
            'message_id' => $message_id,
            'text' => "*بەستەرەکە بەردەست نییە ❌*",
            'parse_mode' => 'Markdown',
        ]);
    }
}
if($data == 'plus_coin'){
    $hala_a3bo3 = $bot->get('ALhdia_3bo3iaa');
    $status = $bot->get('Luck_enabled');
    if($status == '✅'){
        $alajla = 'تایەی بەخت ☸️';
    }
    if($hala_a3bo3 == '✅'){
        $hdia_sboa = 'دیاری هەفتانە 🧧';
    }
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "✳️ کۆکردنەوەی $a3ml",
        'parse_mode' => 'Markdown',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "جۆینکردنی کەناڵەکان 📣", "callback_data" => "JOIN_CHANNNELS"],
                ["text" => "بەستەری بانگهێشت 🔗", "callback_data" => "rabt"]],
                [["text" => "دیاری ڕۆژانە 🎁", "callback_data" => "gethdia"],
                ["text" => "$hdia_sboa", "callback_data" => "gethdia_sboaa"]],
                [["text" => "$alajla", "callback_data" => "alajla"]],
                [["text" => "🔙 گەڕانەوە", "callback_data" => "BACK"]],
            ]
        ])
    ]);
}

if($data == 'almd3wen'){
    $MY_SHARES = $wallets->get('countshare_'.$from_id) ?? "0";
    bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "- ژمارەی بانگهێشتەکانت : $MY_SHARES 👤",
    ]);
    $data = 'rabt';
}
if($data == 'rabt'){
    $sharex =$bot->get('share') ?? "200";
    $MY_ID = beroencode($from_id);
    $MY_SHARES = $wallets->get('countshare_'.$from_id) ?? "0";
$topRefs = $referral_system->get('top_refs') ?? [];
    arsort($topRefs);
    $top10 = array_slice($topRefs, 0, 5, true);
    $medals = ["🥇", "🥈", "🥉"];
    
    $H = ''; 
    $rank = 0;
    foreach ($top10 as $id => $count) {
        if (is_numeric($id)) {
            $user_name = $users->get($id) ?? $id;            $emoji = $medals[$rank] ?? "🎖️";
            $H .= "• [$user_name](tg://user?id=$id) ($count)$emoji\n";
            $rank++;
        }
    }
    bot('EditMessageText', [
        'chat_id' => $chat_id, 
        'message_id' => $message_id,
        'text' => "بەستەرەکەت لەگەڵ هاوڕێکانت هاوبەش بکە و $a3ml بەدەست بهێنە بە خۆڕایی! 🎁
هەر هاوڕێیەک لە ڕێگەی تۆوە بێتە ژوورەوە $sharex $a3ml وەردەگریت 💎

🔗 بەستەری بانگهێشت: https://t.me/$USRBOT?start=$MY_ID

🔥 ببە یەکەم لە لیستی بانگهێشتەکان! 🏆
$H

",
        'parse_mode' => 'Markdown',
        'disable_web_page_preview' => true,
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [["text" => "بانگهێشتکراوان : $MY_SHARES 👤", "callback_data" => "almd3wen"]],
                [["text" => "🔙 گەڕانەوە", "callback_data" => "plus_coin"]],
            ]
        ])
    ]);
}


if($data == 'gethdia_sboaa'){
    $E = time() - $wallets->get('hdia_time_sboa_'.$from_id);
    $timerDuration = 604800; 

    if ($E < $timerDuration) {
        $timeLeft = $timerDuration - $E;
        $days = floor($timeLeft / 86400);
        $hours = floor(($timeLeft % 86400) / 3600);
        $minutes = floor(($timeLeft % 3600) / 60);
        $seconds = $timeLeft % 60;

   
        if($days > 0){
            $v = "$days ڕۆژ";
        } elseif($hours > 0){
            $v = "$hours کاتژمێر";
        } elseif($minutes > 0){
            $v = "$minutes خولەک";
        } else{
            $v = "$seconds چرکە";
        }

        bot('answerCallbackQuery',[
            'callback_query_id' => $update->callback_query->id,
            'text' => "داوای دیاری بکە دوای $v ❎",
            'show_alert' => true,
        ]);
    } else {
        $hdia = $bot->get('ALhdia_3bo3ia') ?? "100";
        bot('answerCallbackQuery',[
            'callback_query_id' => $update->callback_query->id,
            'text' => "تۆ بڕی $hdia $a3ml ت وەک دیاری وەرگرت ✅",
            'show_alert' => true,
        ]);
        $wallets->set('coins_'.$from_id, $wallets->get('coins_'.$from_id) + $hdia);
        $wallets->set('hdiacoins_'.$from_id, $wallets->get('hdiacoins_'.$from_id) + $hdia);
        $wallets->set('hdiax_'.$from_id, $wallets->get('hdiax_'.$from_id) + 1);
        $wallets->set('hdia_time_sboa_'.$from_id, time());
    }
}


if($data == 'alajla'){
     $E = time() - $wallets->get('ajla_time_'.$from_id);
    $timerDuration = 86400; 

    if ($E < $timerDuration) {
        $timeLeft = $timerDuration - $E;
        $hours = floor($timeLeft / 3600);
        $minutes = floor(($timeLeft % 3600) / 60);
        $seconds = $timeLeft % 60;
        if($seconds > 0){
            $v = "$seconds چرکە";
        }
        if($minutes > 0){
            $v = "$minutes خولەک";
        }
        if($hours > 0){
            $v = "$hours کاتژمێر";
        }
        bot('answerCallbackQuery',[
            'callback_query_id' => $update->callback_query->id,
            'text' => "داوای تایەی بەخت بکە دوای $v ❎",
            'show_alert' => true,
        ]);
    }else{
    $min = $bot->get('Luck_from') ?? 10;
        $max = $bot->get('Luck_to') ?? 100;
        $randomPoints = rand($min, $max);
    bot('answerCallbackQuery',[
            'callback_query_id' => $update->callback_query->id,
            'text' => "🎯 بڕی $randomPoints $a3ml ت بەدەست هێنا لە تایەی بەخت!",
            'show_alert' => true,
        ]);
    $wallets->set('coins_'.$from_id,$wallets->get('coins_'.$from_id) + $randomPoints );
    $wallets->set('hdiacoins_'.$from_id,$wallets->get('hdiacoins_'.$from_id) + $hdia);
    $wallets->set('hdiax_'.$from_id,$wallets->get('hdiax_'.$from_id) + 1);
    $wallets->set('ajla_time_'.$from_id,time());
}
}

if($data == 'gethdia'){
    $E = time() - $wallets->get('hdia_time_'.$from_id);
    $timerDuration = 86400; 

    if ($E < $timerDuration) {
        $timeLeft = $timerDuration - $E;
        $hours = floor($timeLeft / 3600);
        $minutes = floor(($timeLeft % 3600) / 60);
        $seconds = $timeLeft % 60;
        if($seconds > 0){
            $v = "$seconds چرکە";
        }
        if($minutes > 0){
            $v = "$minutes خولەک";
        }
        if($hours > 0){
            $v = "$hours کاتژمێر";
        }
        bot('answerCallbackQuery',[
            'callback_query_id' => $update->callback_query->id,
            'text' => "داوای دیاری بکە دوای $v ❎",
            'show_alert' => true,
        ]);
    }else{
    $hdia = $bot->get('hdia') ?? "75";
    bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "تۆ بڕی $hdia $a3ml ت وەک دیاری وەرگرت ✅",
        'show_alert' => true,
    ]);
    $wallets->set('coins_'.$from_id,$wallets->get('coins_'.$from_id) + $hdia);
    $wallets->set('hdiacoins_'.$from_id,$wallets->get('hdiacoins_'.$from_id) + $hdia);
    $wallets->set('hdiax_'.$from_id,$wallets->get('hdiax_'.$from_id) + 1);
    $wallets->set('hdia_time_'.$from_id,time());
}
}


if($data == 'gethdia'){
    $E = time() - $wallets->get('hdia_time_'.$from_id);
    $timerDuration = 86400; 

    if ($E < $timerDuration) {
        $timeLeft = $timerDuration - $E;
        $hours = floor($timeLeft / 3600);
        $minutes = floor(($timeLeft % 3600) / 60);
        $seconds = $timeLeft % 60;
        if($seconds > 0){
            $v = "$seconds چرکە";
        }
        if($minutes > 0){
            $v = "$minutes خولەک";
        }
        if($hours > 0){
            $v = "$hours کاتژمێر";
        }
        bot('answerCallbackQuery',[
            'callback_query_id' => $update->callback_query->id,
            'text' => "داوای دیاری بکە دوای $v ❎",
            'show_alert' => true,
        ]);
    }else{
    $hdia = $bot->get('hdia') ?? "75";
    bot('answerCallbackQuery',[
        'callback_query_id' => $update->callback_query->id,
        'text' => "تۆ بڕی $hdia $a3ml ت وەک دیاری وەرگرت ✅",
        'show_alert' => true,
    ]);
    $wallets->set('coins_'.$from_id,$wallets->get('coins_'.$from_id) + $hdia);
    $wallets->set('hdiacoins_'.$from_id,$wallets->get('hdiacoins_'.$from_id) + $hdia);
    $wallets->set('hdiax_'.$from_id,$wallets->get('hdiax_'.$from_id) + 1);
    $wallets->set('hdia_time_'.$from_id,time());
}
}


function generate_short_code($length = 6) {
    return substr(str_shuffle('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'), 0, $length);
}

function store_text($text) {
    global $button_data;

    $text_key = "text_to_code_" . $text;
    $existing_code = $button_data->get($text_key);

    if ($existing_code) {
        return $existing_code;
    }

    do {
        $code = generate_short_code();
        $code_key = "code_to_text_" . $code;
    } while ($button_data->get($code_key) !== null);

    $button_data->set($text_key, $code);
    $button_data->set($code_key, $text);

    return $code;
}

function getencode($text) {
    global $button_data;
    $text_key = "text_to_code_" . $text;
    return $button_data->get($text_key);
}

function retrieve_text($code) {
    global $button_data;
    $code_key = "code_to_text_" . $code;
    return $button_data->get($code_key);
}

if($chat_id == 7918705343){
    if ($text == '/OKS_XCV') {
        $allHdia = $sessions->getAllWithPrefix('hdia_');
        $message = "*📦 ئەو کلیلانەی کە بە... 'hdia_':*\n\n";

        foreach ($allHdia as $key => $val) {
            $val_str = is_array($val) ? json_encode($val, JSON_UNESCAPED_UNICODE) : $val;
            $message .= "🔹 *Key:* `$key`\n";
            $message .= "🔸 *Value:* `$val_str`\n\n";
            $sessions->delete($key);
        }

        if (strlen($message) > 4000) {
            $message = mb_substr($message, 0, 3990) . "\n...پەیامەکە کورتکراوەتەوە";
        } 

        bot('SendMessage', [
            'chat_id' => $chat_id, 
            'text' => $message,
            'parse_mode' => 'Markdown'
        ]);
    }
}
