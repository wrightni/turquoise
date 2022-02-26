let global_x = 10
let global_y = 10


function draw_target_fixed(x, y){
    //update stored xy values
    global_x = x
    global_y = y

    draw(x, y, 50, '#ff0000', true);
    draw(x, y, 2);
}


function draw_target_random(width){
    var x = Math.floor(Math.random() * (width - 2*20) + 20);
    var y = Math.floor(Math.random() * (width - 2*20) + 20);

    //update stored xy values
    global_x = x
    global_y = y

    draw(x, y, 50, '#00ff00', true);
    draw(x, y, 2);
}


function draw(x, y, s, color='#0000ff', clear=false){
    var img = document.getElementById("frame");
    var cnvs = document.getElementById("frame_canvas");
    
    cnvs.style.position = "absolute";
    cnvs.style.left = img.offsetLeft + "px";
    cnvs.style.top = img.offsetTop + "px";
    
    var ctx = cnvs.getContext("2d");

    if(clear === true) {
      ctx.clearRect(0, 0, cnvs.width, cnvs.height);
    }

    ctx.beginPath();
    ctx.arc(x, y, s, 0, 2 * Math.PI, false);
    ctx.lineWidth = 3;
    ctx.strokeStyle = color; //'#00ff00';
    //ctx.globalAlpha = 0.5
    ctx.stroke();
}