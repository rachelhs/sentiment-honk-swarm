
$(document).ready(function(){
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');

    //receive details from server
    socket.on('newnumber', function(msg) {
        console.log("Received number " + msg.number);
        $('#log').html(msg.number);
    });

    socket.on('newscore', function(msg) {
        console.log("Received score " + msg.score);
        $('#score').html(msg.score);
    });

});