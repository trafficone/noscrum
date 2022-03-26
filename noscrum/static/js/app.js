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

var create_task = function(
    task_json,
    callback)
    {
        task_name = $('<div>').addClass('task-name')
                .addClass('columns')
                .addClass('small-8')
                .html(
                    $('<span>').addClass('editable')
                    .attr('title','Click to Edit Task')
                    .attr('id','task_name_'+task_json.id)
                    .attr('update_key','task')
                    .text(task_json.task)
                );
        task_status = $('<div>').addClass('columns')
                .addClass('small-2')
                .addClass('label')
                .addClass('float-right')
                .addClass('status')
                .addClass(task_json.status.toLowerCase().replaceAll(' ','-'))
                .attr('style','margin-right:1rem;')
                .attr('id','task_status_'+task_json.id)
                .text(task_json.status);
        task_estimate = $('<div>').addClass('columns')
                .addClass('small-2')
                .html('E:&nbsp;'+
                    $('<span>').addClass('editable')
                    .addClass('note')
                    .addClass('estimate')
                    .attr('title','Click to Edit Estimate')
                    .attr('id','task_est_'+task_json.id)
                    .attr('update_key','estimate')
                    .attr('placeholder','None')
                    .text(task_json.estimate == undefined ? 'None' : task_json.estimate)
                    .prop('outerHTML')
                );
        task_actual = $('<div>').addClass('columns')
                    .addClass('small-2')
                    .html(
                        $('<span>').addClass('float-right')
                        .text('A:'+(task_json.actual == undefined ? 'None' : task_json.actual))
                    );
        datepicker_input = $('<input>').addClass('datepicker-input')
                    .attr('id','task_deadline_'+task_json.id+'_datepicker')
                    .attr('name','date')
                    .attr('type','hidden');
        task_deadline = $('<span>').addClass('task-deadline')
                    .addClass('editable')
                    .addClass('deadline')
                    .attr('title','Click to Edit')
                    .attr('contentEditable','false')
                    .attr('update_key','deadline')
                    .attr('id','task_deadline_'+task_json.id)
                    .text(task_json.deadline == undefined ? 'No Deadline Set' : task_json.deadline)
        task_sprint_status = $('<span>').addClass('float-right')
                    .attr('id','task_sprint_status_'+task_json.id);
        recurring = $('<div>').addClass('recurring')
                    .addClass('columns')
                    .addClass('small-2')
                    .addClass('label')
                    .addClass('float-right')
                    .attr('style','margin-right:1rem;')
                    .attr('title','Click to Edit')
                    .text(task_json.recurring ? 'Recurring' : 'One-Time');
        
        var get_sprint_plan_button = function(){
                        if (task_json.status != 'Done') {
                            return $('<button>').addClass('sprintPlan')
                            .addClass('button')
                            .addClass('float-right')
                            .addClass('invisible')
                            .attr('style','margin:0.1rem;padding:0.2em 1em;')
                            .attr('id','task_sprint_btn_'+task_json.id)
                            .attr('task',task_json.id)
                            .text('Add to Sprint')
                        }
                    };
        // Sprint Board-Specific
        task_epic = $('<div>').addClass('epic-label')
                    .addClass('columns')
                    .addClass('small-2')
                    .text(task_json.epic);
        task_story = $('<div>').addClass('story-label')
                    .addClass('columns')
                    .addClass('small-6')
                    .text(task_json.story);
        task_schedule = $('<div>').addClass('label')
                        .addClass('small-2')
                        .addClass('columns')
                        .addClass('label');
        new_task = $('<div>').addClass('task-container')
        .addClass('container')
        .attr('update_url','/task/'+task_json.id+'?is_json=true')
        .html(
            $('<div>').addClass('task-header')
            .addClass('row')
            .html(task_name)
            .append(
                $('<div>').addClass('columns')
                .addClass('small-4')
            ).append(
                    task_status
            ).append($('<br>'))
        ).append(
            $('<div>').addClass('task-work')
            .addClass('row')
            .html(task_estimate)
            .append(task_actual)
            .append(
                    $('<div>').addClass('columns')
                    .addClass('small-8')
                    .html(datepicker_input)
                    .append(task_deadline)
                    .append(get_sprint_plan_button())
                    .append(task_sprint_status)
                    
            )
            .append(recurring)
        );
        return callback(new_task);
    };

    var selectCurrentWeek = function() {
        window.setTimeout(function () {
            $('.week-picker').find('.ui-datepicker-current-day a').addClass('ui-state-active')
        }, 1);
    }