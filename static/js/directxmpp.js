var connection = null;
var nick = null;

function printMessage(msg) 
{
    $('#output').append('<p>'+msg+'</p>');
    $('#output').scrollTop( $('#output')[0].scrollHeight );
}

function onConnect(status)
{
    if (status == Strophe.Status.CONNECTING) {
	printMessage('Connecting...');
    } else if (status == Strophe.Status.CONNFAIL) {
	printMessage('Failed to connect.');
	$('#connect').get(0).value = 'connect';
    } else if (status == Strophe.Status.DISCONNECTING) {
	printMessage('Disconnecting...');
    } else if (status == Strophe.Status.DISCONNECTED) {
	printMessage('Disconnected.');
	$('#connect').get(0).value = 'connect';
	$('#chat').hide();
    } else if (status == Strophe.Status.CONNECTED) {
	printMessage('Connected.');
	sendNickname();

	$('#chat').show();
	$('#message').focus();

	connection.addHandler(onMessage, null, 'message', null, null,  null); 
	connection.send($pres().tree());
    }
}

function onMessage(msg) {
    var to = msg.getAttribute('to');
    var from = msg.getAttribute('from');
    var type = msg.getAttribute('type');
    var elems = msg.getElementsByTagName('body');

    if (type == "chat" && elems.length > 0) {
	var body = elems[0];

	printMessage(from + ': ' + 
	    Strophe.getText(body));
    
    }
    return true;
}

function sendNickname( ) {
    if (connection.connected && connection.authenticated && nick.length > 0) {
	var from = connection.jid;
	var msg = $msg({to: to, from: from, type: 'chat' })
            .c('body').t( 'PenguBytes: ' + nick + ' connected.');
	connection.send(msg.tree());
    }
}

function sendMessage( ) {
    var text = $('#message').get(0).value;
    if (connection.connected && connection.authenticated && text.length > 0) {
	var from = connection.jid;
    
	var msg = $msg({to: to, from: from, type: 'chat'})
            .c('body').t(text);
	connection.send(msg.tree());

	printMessage(nick + ': ' + text);
        $('#message').get(0).value = "";
    }
}

$(document).ready(function () {
    connection = new Strophe.Connection(BOSH_SERVICE);
    
    $('#connect').bind('click', function () {
	var button = $('#connect').get(0);
	if (button.value == 'connect') {
	    nick = $('#nick').get(0).value;
	    if ( nick.length > 0 ) {
	    	button.value = 'disconnect';

	   	connection.connect('anon.pengubytes.de',
			       null,
			       onConnect);
	    } else {
		// don't use alerts
		$('#instruction').html("You have to enter your name to connect.");
	    }
	} else {
	    button.value = 'connect';
	    connection.disconnect();
	}
    });
    $('#send').bind('click', function () {
	sendMessage(  );
    });
});
