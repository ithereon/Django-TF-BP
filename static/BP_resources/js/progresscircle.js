function makesvg(percentage, inner_text=""){

  var abs_percentage = Math.abs(percentage).toString();
  var percentage_str = percentage.toString();
  var classes = ""

  if(percentage < 0){
    classes = "danger-stroke circle-chart__circle--negative";
  } 
  else if(percentage > 0 && percentage < 10){
    classes = "grey-stroke";
  }  
  else if(percentage > 10 && percentage < 20){
    classes = "darkred-stroke";
  }  
  else if(percentage > 20 && percentage < 30){
    classes = "red-stroke";
  }  
  else if(percentage > 30 && percentage <= 40){
    classes = "purple-stroke";
  } 
  else if(percentage > 40 && percentage <= 50){
    classes = "darkblue-stroke";
  } 
  else if(percentage > 50 && percentage <= 60){
    classes = "blue-stroke";
  } 
  else if(percentage > 60 && percentage <= 70){
    classes = "lightblue-stroke";
  } 
  else if(percentage > 70 && percentage <= 80){
    classes = "yellow-stroke";
  } 
  else if(percentage > 80 && percentage <= 90){
    classes = "yellowgreen-stroke";
  } 
  else if(percentage > 90 && percentage <= 100){
    classes = "brightgreen-stroke";
  } 
  else{
    classes = "grey-stroke";
  }

 var svg = '<svg class="circle-chart" viewbox="0 0 33.83098862 33.83098862" xmlns="http://www.w3.org/2000/svg">'
     + '<circle class="circle-chart__background" cx="16.9" cy="16.9" r="15.9" />'
     + '<circle class="circle-chart__circle '+classes+'"'
     + 'stroke-dasharray="'+ abs_percentage+',100"    cx="16.9" cy="16.9" r="15.9" />'
     + '<g class="circle-chart__info">'
     + '   <text class="circle-chart__percent" x="17.9" y="13.5">'+percentage_str+'%</text>';

  if(inner_text){
    svg += '<text class="circle-chart__subline" x="16.91549431" y="22">'+inner_text+'</text>'
  }
  
  svg += ' </g></svg>';
  
  return svg
}

(function( $ ) {

    $.fn.circlechart = function() {
        this.each(function() {
            var percentage = $(this).data("percentage");
            var inner_text = $(this).text();
            $(this).html(makesvg(percentage, inner_text));
        });
        return this;
    };

}( jQuery ));