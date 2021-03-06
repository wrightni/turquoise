
function createParagraph(elem_id){
  const para = document.createElement('p');
  para.textContent = global_x.toString() + '  ' + global_y.toString() + '  ' + elem_id;
  document.body.appendChild(para);
}

function post_data(data) {
  $.ajax({
      type: "POST",
      url: "/assign",
      data: JSON.stringify(data),
      contentType: "application/json",
      dataType: 'json',
      success: function(result) {
        console.log("Result:");
        console.log(result);
      } 
    });
}

function get_preset(data) {
  $.ajax({
    type: "GET",
    url: "/get_preset",
    data: JSON.stringify(data),
    dataType: 'json',
    success: function(result) {
      console.log("Result:");
      console.log(result);
      if (result.success == true){
        draw_target_fixed(result.x, result.y);
      } else {
        draw_target_random(512);
      };
    } 
  });
}

function next_target() {
    if(Math.random() > 0.5){
      draw_target_random(512);
    } else {
      get_preset(100);
    };
  // 
}

const buttons = document.querySelectorAll('button');

for (const button of buttons) {
  button.addEventListener("click", function() {
      createParagraph(this.id);
      post_data({
          'x': global_x, 
          'y': global_y,
          'clsf': this.id});
      next_target();
  });
}

document.addEventListener("DOMContentLoaded", function() {
  draw_target_random(512);
})