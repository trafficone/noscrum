"use strict";

const cr_elem = React.createElement;

function EditableHandleClick(t, origin) {
  const task_name_obj = origin;
  function callback_func() {
    $(t.target).attr("contentEditable", "false");
    $(t.target).off("keydown");
    $(t.target).off("blur");
  }
  $(t.target).attr("contentEditable", "true");
  $(t.target).focus();
  $(t.target).keydown(function (e) {
    if (e.keyCode === 13) {
      const new_value = $(t.target).text().trim();
      task_name_obj.props.update(new_value, callback_func);
    }
  });
  $(t.target).blur(function (e) {
    const new_value = $(t.target).text().trim();
    task_name_obj.props.update(new_value, callback_func);
  });
}

class TaskStatusButton extends React.Component {
  render() {
    return (
      <div
        className={
          "columns small-2 label float-right status oneOver " +
          this.getStatusClass()
        }
        onClick={
          this.props.update ? () => {this.handleClick();} : ()=>{}
        }
      >
        {this.props.status}
      </div>
    );
  }

  getStatusClass() {
    return this.props.status.toLowerCase().replaceAll(" ", "-");
  }

  handleClick() {
    const status_list = ["To-Do", "In Progress", "Done"];
    const next_status =
      this.props.status == "Done"
        ? "To-Do"
        : status_list[status_list.indexOf(this.props.status) + 1];
    this.props.update(next_status, () => {});
  }
}
class TaskRecurringButton extends React.Component {
  render() {
    return (
      <div
        className={
          "oneOver columns small-2 label recurring " +
          (this.props.recurring ? "recur_color" : "")
        }
        onClick={
            this.props.editable 
                ? () => this.handleClick()
                : ()=>{}}
      >
        {this.props.recurring ? "Recurring" : "One-Time"}
      </div>
    );
  }

  handleClick() {
    const new_recurring = !this.props.recurring;
    this.props.update(new_recurring, () => {});
  }
}
class TaskNameLabel extends React.Component {
  render() {
    return (
      <div className="columns large-6 task-name">
        <span
          className={this.props.update ? "editable" : ""}
          title={this.props.update?"Click to Edit":"Task Name"}
          update_key="task"
          onClick={
            this.props.update
              ? (t) => {
                  EditableHandleClick(t, this);
                }
              : () => {}
          }
        >
          {this.props.task}
        </span>
      </div>
    );
  }
}
class TaskEstimateLabel extends React.Component {
  render() {
    return (
      <div className="columns small-2">
        E:&nbsp;
        <span
          title="Click to Edit Estimate"
          className={"note estimate " + this.props.update ? 'editable' : ''}
          onClick={this.props.update ? (t) => EditableHandleClick(t, this) : ()=>{}}
        >
          {this.props.estimate}
        </span>
      </div>
    );
  }
}
function TaskActualLabel(props) {
    return (
      <div className="columns small-2">
        <span className="float-right">
          A:&nbsp;{props.actual ? props.actual : "None"}
        </span>
      </div>
    );
}
class TaskDeadlineLabel extends React.Component {
  render() {
    return (
      <span>
        <input name="date" className="datepicker-input" type="hidden" />
        <span
          title="Click To Edit"
          //contentEditable="false"
          updatekey="deadline"
          className={"task-deadline deadline "+this.props.update ? 'editable' : ''}
          onClick={
            this.props.update ? (t) => this.handleClick(t) : ()=>{}}
        >
          {this.getDeadlineMessage()}
        </span>
      </span>
    );
  }

  handleClick(t) {
    const date_obj = this;
    $(t.target).attr("contentEditable", "false");
    const datepicker = $(t.target).siblings("input");
    $(datepicker).datepicker({
      firstDay: 1,
      dateFormat: "yy-mm-dd",
      onClose: function (dateText, inst) {
        $(this).siblings(".deadline").focus().html(dateText).blur();
      }
    });
    function callback_func() {
      $(t.target).attr("contentEditable", "false");
      $(t.target).off("keydown");
      $(t.target).off("blur");
      $(datepicker).off("datepicker");
    }
    $(t.target).blur(function (e) {
      const new_value = $(t.target).text().trim();
      date_obj.props.update(new_value, callback_func);
    });
    $(datepicker).focus().focus();
  }

  getDeadlineMessage() {
    if (this.props.deadline === undefined) {
      return this.props.recurring ? "No End Date Set" : "No Deadline Set";
    }
    return this.props.deadline;
  }
}
class TaskSchedulingWidget extends React.Component {
  render() {
    return (
      <div className="columns large-6">
        <TaskDeadlineLabel
          deadline={this.props.deadline}
          recurring={this.props.recurring}
          update={(v, c) => this.props.update("deadline", v, c)}
        />
        <button className="float-right button sprintPlan hidden">
          Add To Sprint
        </button>
        <span className="float-right">{this.get_status_message()}</span>
      </div>
    );
  }

  get_status_message() {
    if (this.props.status == "Done") {
      return "Task Complete";
    } else if (this.props.sprint == "scheduling") {
      return (
        <TaskScheduleButton
          onClick={() => this.props.handleClick("schedule")}
        />
      );
    } else if (this.props.sprint !== undefined) {
      return "Task In Sprint of " + this.props.sprint;
    } else {
      return "Task Not in Sprint";
    }
  }
}
function TaskWorkLabel(props) {
    return (
      <div className="small-6 columns float-right">
        Worked This Day:
        <span className="hours-worked">
          {props.schedule_work ? props.schedule_work : 0}
        </span>
      </div>
    );
}
class TaskWorkButton extends React.Component {
  render() {
    return (
      <div
        title="Click to Log Work"
        className="columns small-2 label float-right log-work"
        onClick={(t) => this.handleClick(t)}
      >
        Log Work
      </div>
    );
  }
  handleClick(t) {
    //TODO: Handle Work Logging Modal
    console.log("Work Log for T:" + t);
    const new_work_val = this.props.schedule_work ? this.props.schedule_work + 2 : 2;
    this.props.update(new_work_val, () => {
      console.log("You worked 2 hours & closed modal");
    });
  }
}
class TaskScheduleNote extends React.Component {
  render() {
   return (
      <div title="Click to Edit Note" className="small-8 columns">
        <span
          className="note"
          title="Schedule-specific Note"
          onClick={this.props.update ? (t) => this.handleClick(t) : ()=>{}}
          >
       {this.props.schedule_note ? this.props.schedule_note : "Schedule-Specific Note"}
          </span>
      </div>
    );
  }
  handleClick(t) {
    if($(t.target).text() == "Schedule-Specific Note"){
      $(t.target).text('')
    }
    EditableHandleClick(t, this)
  }
}
class TaskEpicLabel extends React.Component {
  render() {
    return (
      <div className={"columns small-2 epic-label " + this.props.color}>
        {this.props.epic}
      </div>
    );
  }
}
class TaskStoryLabel extends React.Component {
  render() {
    return (
      <div className="columns small-2 story-label">{this.props.story}</div>
    );
  }
}
class TaskContainerShowcase extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      task: props.task,
      status: props.status,
      estimate: props.estimate,
      deadline: props.deadline,
      recurring: props.recurring ? props.recurring : false,
      sprint: props.sprint
    };
  }
  render() {
    return (
      <div
        className="container task-container"
        task={this.props.id}
        update_url={this.props.update_url}
      >
        <div className="row task-header">
          <TaskNameLabel
            task={this.state.task}
            update={(v, c) => this.handleClick("task", v, c)}
            update_key="task"
          />
          <div className="columns small-4"></div>
          <TaskStatusButton
            status={this.state.status}
            update={(v, c) => this.handleClick("status", v, c)}
          />
        </div>
        <div className="row task-work">
          <TaskEstimateLabel
            estimate={this.state.estimate}
            update={(v, c) => this.handleClick("estimate", v, c)}
            update_key="estimate"
          />
          <TaskActualLabel actual={this.props.actual} />
          <TaskSchedulingWidget
            sprint={this.state.sprint}
            status={this.state.status}
            deadline={this.state.deadline}
            recurring={this.state.recurring}
            update={(t, v, c) => this.handleClick(t, v, c)}
          />
          <TaskRecurringButton
            recurring={this.state.recurring}
            update={(v, c) => this.handleClick("recurring", v, c)}
          />
        </div>
      </div>
    );
  }
  handleClick(target, new_value, callback) {
    //TODO: perform server-side update
    var ntv = Array();
    ntv[target] = new_value;
    console.log(
      "Updated task " + this.props.id + " key '" + target + "' to " + new_value
    );
    this.setState(ntv);
    callback();
  }
}
class TaskContainerSprint extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      status: props.status,
      schedule_work: props.schedule_work,
      schedule_note: props.schedule_note
    };
  }
  render() {
    return (
      <div className="task-container container">
        <div className="row">
          <TaskEpicLabel epic={this.props.epic} color={this.props.color} />
          <TaskStoryLabel story={this.props.story} />
          <TaskNameLabel task={this.props.task} />
          <TaskStatusButton 
                status={this.state.status} 
                update={(v,c)=>this.handleClick('status',v,c)} />
        </div>
        <div className="row">
          <TaskEstimateLabel estimate={this.props.estimate} />
          <TaskWorkLabel schedule_work={this.state.schedule_work} />
          <TaskScheduleNote 
                schedule_note={this.state.schedule_note} 
                update={(v,c)=>this.handleClick('status_note',v,c)} />
          <TaskWorkButton 
                schedule_work={this.state.schedule_work} 
                update={(v,c)=>this.handleClick('schedule_work',v,c)} />
        </div>
      </div>
    );
  }
  handleClick(target, new_value, callback) {
    //TODO: perform server-side update
    var ntv = Array();
    ntv[target] = new_value;
    console.log(
      "Updated task " + this.props.id + " from sprint, key '" + target + "' to " + new_value
    );
    this.setState(ntv);
    callback();
  }
}

/*
const root = ReactDOM.createRoot(document.getElementById("task_showcase_test"));
const toot = ReactDOM.createRoot(
  document.getElementById("sprint_showcase_test")
);
root.render(
  <TaskContainerShowcase
    status="To-Do"
    task="test_task"
    id="5"
    update_url="http://localhost/task"
    estimate="1.0"
  />
); 
toot.render(
  <TaskContainerSprint
    status="To-Do"
    task="test_task2"
    id="7"
    estimate="4"
    epic="CoolGuy"
    update_url="http://localhost/task"
    color="green"
    story="Less Cool"
  />
);*/

class StoryNameLabel extends React.Component{
    render() {
        return (
        <h5 className={this.props.update ? "editable" : ""}
            title={this.props.update ? "Click to Edit Story" : "Story Name"}
            onClick={this.props.update ? (t)=>EditableHandleClick(t,this) : ()=>{}}>
        {this.props.story}
        </h5>
        )
    }
}
class StoryPriorityLabel extends React.Component{
    render () {
        return (
            <div class="float-left">
                <span class={'badge '+this.props.color}
                      title={this.props.update ? 'Click to Edit Priority' : 'Prioritization'}
                      onClick={()=>{}} //TODO: Implement Priority Label Editing
                >
                    {this.props.prioritization}
                </span>
            </div>
        )
    }
}
class StoryArchiveButton extends React.Component{}
class StoryEstimateLabel extends React.Component{
    render(){
        return (<div>
            Hours Estimated: 
            <span class="story-metric estimate">
                {this.props.estimate}
            </span>
        </div>
        )
    }
}
class StorySummaryContainer extends React.Component{
    render(){
        return(
            <div className="row story-summary">
                <StoryEstimateLabel estimate={this.props.estimate} />
                <StoryIncompleteLabel incomplete={this.props.incomplete} />
                <StoryDeadlineLabel deadline={this.props.deadline} update={(v,c)=>this.props.update('deadline',v,c)} />
                <StoryArchiveButton archive={()=>this.props.archive()} />
            </div>
        )
    }
}
class StoryTaskContainer extends ReactComponent{}
class StoryCreateTaskButton extends React.Component{}
class StoryContainer extends React.Component{}

class EpicNameLabel extends React.Component{}
class EpicEstimatesWidget extends React.Component{}
class EpicStoryContainer extends React.Component{}
class EpicCreateStoryButton extends React.Component{}
class EpicContainer extends React.Component{}

class SprintDayLabel extends React.Component{}
class SprintDayEstimateLabel extends React.Component{}
class SprintDayContainer extends React.Component{}
class SprintLabel extends React.Component{}
class SprintEstimate extends React.Component{}
class SprintContainer extends React.Component{}

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