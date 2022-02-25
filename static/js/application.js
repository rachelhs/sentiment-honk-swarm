
$(document).ready(function(){
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');

    //receive details from server
    socket.on('newspeech', function(msg) {
        const random_left = (Math.floor(Math.random() * 180) + 90);
        console.log("Received speech " + msg.speech);
        $('#log').html('heard:  ' + msg.speech);
        new CircleType(document.getElementById('log')).radius(random_left);
        console.log('random left ', random_left);
    });

    socket.on('newscore', function(msg) {
        const random_right = (Math.floor(Math.random() * 180) + 90);
        console.log("Received score " + msg.score);
        $('#score').html('negativity score:  ' + msg.score + '%');
        new CircleType(document.getElementById('score')).radius(random_right).dir(-1);
        console.log('random right ', random_right);
    });

});