$.expander.defaults.slicePoint = 120;

$(document).ready(function() {
  $('.article_text').expander({
    slicePoint:       600,
    expandPrefix:     '... ',
    expandText:       '(more)',
    collapseTimer:    0,
    userCollapseText: '(less)'
  });

});
