$(document).foundation();

var pretty_alert = function(message) {
    $('header').after($('<div>')
        .text(message)
        .append($('<button>')
            .addClass('close-button')
            .attr('data-close','')
            .html('&times;')
            .foundation())
        .addClass('callout alert')
        .attr('data-closable','')
        .foundation()
        );
};