'use strict;'
import { PropTypes } from 'prop-types'
import React from 'react'
import axios from 'axios'
import app from './app.jsx'
import { TaskContainerShowcase, CreateTaskButton } from './task.jsx'

const EditableHandleClick = app.EditableHandleClick
const DeadlineLabel = app.DeadlineLabel

class CreateStory extends React.Component {
  static propTypes = {
    epic: PropTypes.number.isRequired,
    addStory: PropTypes.func.isRequired,
    notOpen: PropTypes.func
  }

  constructor (props) {
    super(props)
    this.state = {
      story: '',
      prioritization: 5
    }
  }

  async createStory () {
    if (this.state.story === undefined) {
      app.PrettyAlert('Cannot Create Unnamed Story')
      return
    }
    await axios.post(`/story/create/${this.props.epic}?is_json=true`, this.state)
      .then((response) => {
        const newStory = response.data.story
        this.props.addStory(newStory)
        this.props.notOpen()
      })
  }

  render () {
    return (
      <div>
        <div className="cell">
          <label>Story
            <input type="text"
                name="story"
                id="story"
                aria-describedby="exampleHelpStory"
                onChange={(v) => this.setState({ ...this.state, story: v.target.value })}
                data-abide-ignore
                required />
          </label>
          <p className="help-text" id="exampleHelpStory">Name of Story You are Creating.</p>
        </div>
        <div className="cell medium-6">
          <label>
            Prioritization
            <select id="prioritization"
              name="prioritization"
              onChange={(v) => this.setState({ ...this.state, prioritization: v.target.value })}
            required>
            <option value="5">5 - Critical</option>
            <option value="4">4 - High</option>
            <option value="3">3 - Medium</option>
            <option value="2">2 - Low</option>
            <option value="1">1 - No Priority</option>
          </select>
        </label>
      </div><div>
          <button className="button float-left" onClick={() => this.createStory()}>Create</button>
          <button className="button cancel float-right" onClick={() => this.props.notOpen()}>Cancel</button>
        </div>
      </div>
    )
  }
}

class CreateStoryButton extends React.Component {
  static propTypes = {
    addStory: PropTypes.func.isRequired,
    epic: PropTypes.number.isRequired
  }

  constructor (props) {
    super(props)
    this.state = {
      open: false
    }
  }

  notOpen () {
    this.setState({ open: false })
  }

  render () {
    let content = (
      <button
        className="button create create-story"
        onClick={() => { this.setState({ open: true }) }}
      >
        Create Story
      </button>)
    if (this.state.open) {
      content = (<CreateStory epic={this.props.epic} addStory={(v) => this.props.addStory(v)} notOpen={() => this.notOpen()} />)
    }
    return (
      <div>
        {content}
      </div>
    )
  }
}

class StoryNameLabel extends React.Component {
  static propTypes = {
    update: PropTypes.func,
    story: PropTypes.string.isRequired
  }

  render () {
    return (
      <h5
        className={this.props.update ? 'editable' : ''}
        title={this.props.update ? 'Click to Edit Story' : 'Story Name'}
        onClick={
          this.props.update ? (t) => EditableHandleClick(t, this) : () => {}
        }
      >
        {this.props.story}
      </h5>
    )
  }
}

class StoryPriorityLabel extends React.Component {
  static propTypes = {
    update: PropTypes.func,
    prioritization: PropTypes.number
  }

  render () {
    return (
      <div className="float-left">
        <span
          className={'badge priority_' + this.props.prioritization}
          title={
            this.props.update ? 'Click to Edit Priority' : 'Prioritization'
          }
          onClick={() => {}} // TODO: Implement Priority Label Editing
        >
          {this.props.prioritization}
        </span>
      </div>
    )
  }
}

class StoryArchiveButton extends React.Component {
  static propTypes = {
    archive: PropTypes.bool,
    update: PropTypes.func
  }

  render () {
    return (
      <button
        className="button close-story"
        onClick={() => this.handleArchive()}
      >
        {this.props.archive ? 'Reopen' : 'Archive'} Story
      </button>
    )
  }

  handleArchive () {
    // TODO: Handle Archive
  }
}

class StoryEstimateLabel extends React.Component {
  static propTypes = {
    estimate: PropTypes.number
  }

  render () {
    return (
      <div>
        Hrs Estimated:
        <span className="story-metric estimate">{this.props.estimate}</span>
      </div>
    )
  }
}

function StoryIncompleteLabel (props) {
  return (
    <div>
      Tasks to Finish:
      <span className="story-metric estimate">{props.incomplete}</span>
    </div>
  )
}
StoryIncompleteLabel.propTypes = { incomplete: PropTypes.number }

class StorySummaryContainer extends React.Component {
  static propTypes = {
    estimate: PropTypes.number,
    incomplete: PropTypes.number,
    deadline: PropTypes.string,
    update: PropTypes.func,
    archive: PropTypes.bool
  }

  render () {
    return (
      <div className="small-2  cell story-label">
        <StoryEstimateLabel estimate={this.props.estimate} />
        <StoryIncompleteLabel incomplete={this.props.incomplete} />
        <DeadlineLabel
          deadline={this.props.deadline}
          update={(v, c) => {
            this.props.update(v, () => {
              console.log('Updating to ' + v)
              c()
            })
          }}
        />
        <StoryArchiveButton update={this.props.update} />
      </div>
    )
  }
}
class StoryTasksContainer extends React.Component {
  static propTypes = {
    tasks: PropTypes.array,
    update: PropTypes.func,
    filterObject: PropTypes.object,
    planningSprint: PropTypes.string
  }

  render () {
    const tasks = this.props.tasks
    const taskContainers = tasks.map((task) => (
      <TaskContainerShowcase
        key={task.id}
        id={task.id}
        status={task.status}
        task={task.task}
        estimate={task.estimate}
        deadline={task.deadline}
        recurring={task.recurring}
        sprint={task.sprint}
        update={(s, v, c) => this.props.update(task.id, s, v, c)}
        filterObject={this.props.filterObject}
        planningSprint={this.props.planningSprint}
      />
    ))
    return <div className="containers">{taskContainers}</div>
  }
}

class StoryContainerTShowcase extends React.Component {
  static propTypes = {
    id: PropTypes.number.isRequired,
    story: PropTypes.string.isRequired,
    prioritization: PropTypes.number,
    deadline: PropTypes.string,
    tasks: PropTypes.array,
    update: PropTypes.func,
    updateTask: PropTypes.func,
    filterObject: PropTypes.object,
    planningSprint: PropTypes.string
  }

  constructor (props) {
    super(props)

    this.state = {
      task: this.props.tasks,
      hasError: false
    }
  }

  // eslint-disable-next-line n/handle-callback-err
  static getDerivedStateFromError (error) {
    return { hasError: true }
  }

  render () {
    if (this.state.hasError) {
      return (
        <div className='epic '>
          <span><i className="fi-alert"></i>An error occurred in this component. Please refresh page.</span>
        </div>
      )
    }
    const tasks = this.state.task
    const totalEstimate = tasks.reduce((acc, task) => {
      return acc + Number(task.estimate ? task.estimate : 0)
    }, 0)
    const incompleteTasks = tasks.reduce((acc, task) => {
      return acc + Number(task.satuts === 'Done' ? 0 : 1)
    }, 0)
    return (
      <div>
      <div className="grid-x story">
          <StoryPriorityLabel
            prioritization={this.props.prioritization}
            update={(v, c) => this.props.update('prioritization', v, c)}
          />
          <StoryNameLabel
            story={this.props.story}
            update={(v, c) => this.props.update('story', v, c)}
          />
        </div>
        <div className="grid-x summary-story">
          <StorySummaryContainer
            estimate={totalEstimate}
            incomplete={incompleteTasks}
            deadline={this.props.deadline}
            update={(v, c) => this.props.update('deadline', v, c)}
            archive={true}
          />

          <div className=" cell large-10">
          <StoryTasksContainer
            tasks={tasks}
            update={(t, s, v, c) => this.props.updateTask(t, s, v, c)}
            filterObject={this.props.filterObject}
            planningSprint={this.props.planningSprint}/>
          <CreateTaskButton addTask={(s) => this.addTask(s)} story={this.props.id} />
          </div>
        </div>
      </div>
    )
  }

  addTask (task) {
    const newState = this.state
    newState.task.push(task)
    this.setState(newState)
  }
}

export {
  StoryContainerTShowcase,
  CreateStoryButton
}
