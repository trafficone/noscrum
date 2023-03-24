'use strict;'
import { PropTypes } from 'prop-types'
import React from 'react'
import app from './app.jsx'
import { StoryContainerTShowcase, CreateStoryButton } from './story.jsx'
import axios from 'axios'

const AjaxUpdateProperty = app.AjaxUpdateProperty
const AjaxDelete = app.AjaxDelete
const GetUpdateURL = app.GetUpdateURL
const GetCloseURL = app.GetCloseURL
const EditableHandleClick = app.EditableHandleClick

class CreateEpic extends React.Component {
  static propTypes = {
    addEpic: PropTypes.func,
    notOpen: PropTypes.func
  }

  constructor (props) {
    super(props)
    this.state = {
      epic: '',
      color: ''
    }
  }

  setEpic (epic) {
    const newState = this.state
    newState.epic = epic.target.value
    this.setState(newState)
  }

  setColor (color) {
    const newState = this.state
    newState.color = color.target.value
    this.setState(newState)
  }

  async createEpic () {
    console.log('Creating Epic ' + this.state.epic)
    if (this.state.epic === undefined) {
      app.PrettyAlert('Cannot Crate Unnamed Epic')
      return
    }
    await axios.post('/epic/create?is_json=true', this.state).then((response) => {
      const epic = response.data.epic
      this.props.addEpic(epic)
      this.props.notOpen()
    })
  }

  render () {
    return (
      <div className="cell">
          <label>Epic Name
              <input type="text"
                placeholder="Thesis"
                aria-describedby="exampleHelpEpic"
                name="epic"
                id="epic"
                onChange={(v) => this.setEpic(v)}
                value={this.state.epic}
                required />
          </label>
          <p className="help-text" id="exampleHelpEpic">This is the Epic Name</p>
          <div className="cell medium-6">
              <label>Color
                  <select id="select" name="color" onChange={(v) => this.setColor(v)} required>
                  <option value="green">Green</option>
                  <option value="red">Red</option>
                  <option value="blue">Blue</option>
                  <option value="orange">Orange</option>
                  <option value="purple">Purple</option>
              </select>
              </label>
          </div>
          <div>
              <button className="button" onClick={() => this.createEpic()}>Create</button>
              <button onClick={() => this.props.notOpen() } className="button cancel float-right" type="button" >Cancel</button>
          </div>
      </div>
    )
  }
}

class CreateEpicButton extends React.Component {
  static propTypes = {
    addEpic: PropTypes.func
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
        className="button create create-epic"
        onClick={() => { this.setState({ open: true }) }}
      >
        Create Epic
      </button>)
    if (this.state.open) {
      content = (<CreateEpic addEpic={(v) => this.props.addEpic(v)} notOpen={() => this.notOpen()}></CreateEpic>)
    }
    return (
      <div>
        {content}
      </div>
    )
  }
}

class EpicNameLabel extends React.Component {
  static propTypes = {
    update: PropTypes.func,
    epic: PropTypes.string.isRequired
  }

  render () {
    return (
      <h3 className="editable" onClick={(t) => EditableHandleClick(t, this)}>{this.props.epic}</h3>
    )
  }
}

function EpicEstimateLabel (props) {
  return (
    <div className=" cell small-3">
      {props.label}:&nbsp;<span className="epic-metric">{props.value}</span>
    </div>
  )
}
EpicEstimateLabel.propTypes = { value: PropTypes.number.isRequired, label: PropTypes.string.isRequired }

class EpicEstimatesWidget extends React.Component {
  static propTypes = {
    tasks: PropTypes.array,
    isActive: PropTypes.bool,
    onClick: PropTypes.func
  }

  render () {
    const tasks = this.props.tasks
    const estimates = {
      'Hours Estimated': tasks.reduce((acc, task) => {
        return acc + Number(task.estimate ? task.estimate : 0)
      }, 0),
      'Total Tasks': tasks.length,
      'Tasks to Finish': tasks.reduce((acc, task) => {
        return acc + Number(task.status === 'Done' ? 0 : 1)
      }, 0),
      'Tasks w/o Est': tasks.reduce((acc, task) => {
        return acc + Number(task.estimate === undefined ? 1 : 0)
      }
      , 0)
    }
    const estimateLabels = Object.entries(estimates).map((k, v) => {
      return (<EpicEstimateLabel label={k[0]} key={v} value={k[1]} />)
    })
    return (
      <div className="cell auto estimates-widget" title="Click to Show Stories" onClick={() => this.props.onClick()}>
        {estimateLabels}
      </div>
    )
  }
}

class EpicStoriesContainer extends React.Component {
  static propTypes = {
    updateTask: PropTypes.func,
    updateStory: PropTypes.func,
    closeStory: PropTypes.func,
    stories: PropTypes.array,
    isActive: PropTypes.bool,
    isArchive: PropTypes.bool
  }

  render () {
    const stories = this.props.stories
    const storyVerb = stories.length !== 1 ? 'are' : 'is'
    const storyNoun = stories.length !== 1 ? 'stories' : 'story'
    if (!this.props.isActive) {
      return (
        <div className="grid-x">
          <div className="cell auto"></div>
          <div className="cell shrink"><small>There {storyVerb} {stories.length} {storyNoun} in this epic.</small></div>
        </div>
      )
    }
    const storyContainers = stories.map((story) => {
      return (
        <StoryContainerTShowcase
          key={story.id}
          id={story.id}
          prioritization={story.prioritization}
          story={story.story}
          deadline={story.deadline}
          tasks={story.tasks}
          close={(v, c) => this.props.closeStory(story.id, v, c)}
          update={(s, v, c) => this.props.updateStory(story.id, s, v, c)}
          updateTask={(t, s, v, c) => this.props.updateTask(story.id, t, s, v, c)}
          isArchive={this.props.isArchive}
        />
      )
    })
    return (
      <div>
        {storyContainers}
      </div>
    )
  }
}

class EpicContainer extends React.Component {
  static propTypes = {
    id: PropTypes.number.isRequired,
    oEpic: PropTypes.string.isRequired,
    oColor: PropTypes.string,
    oStories: PropTypes.array,
    isArchive: PropTypes.bool
  }

  constructor (props) {
    super(props)
    const origColor = props.oColor ? props.oColor : 'green'
    this.state = {
      epic: props.oEpic,
      color: origColor,
      story: props.oStories,
      hasError: false,
      isActive: false
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
    const stories = this.state.story
    const tasksAgg = stories.reduce((agg, story) => {
      return agg.concat(story.tasks)
    }, [])
    return (
      <div className={'epic ' + this.state.color}>
        <div className="grid-x">
          <EpicNameLabel
            epic={this.state.epic}
            update={(c, v) => this.handleClick('epic', c, v)}
          />
          <EpicEstimatesWidget tasks={tasksAgg}
            isActive={this.state.isActive}
            onClick={() => this.accordionStories()}/>
          <div className="cell shrink h1" onClick={() => this.accordionStories()}>
            { this.state.isActive ? 'v' : '>' }
          </div>
        </div>
        <EpicStoriesContainer
          stories={stories}
          closeStory={(st, v, c) => this.close('story', st, v, c)}
          updateStory={(st, s, v, c) => this.handleStoryClick(st, s, v, c)}
          updateTask={(st, t, s, v, c) => this.handleTaskClick(st, t, s, v, c)}
          isActive={this.state.isActive}
          isArchive={this.props.isArchive}/>
        <CreateStoryButton addStory={(s) => this.addStory(s)} epic={this.props.id}/>
      </div>
    )
  }

  accordionStories () {
    this.setState({ ...this.state, isActive: !this.state.isActive })
  }

  addStory (story) {
    const newState = this.state
    newState.story.push(story)
    this.setState(newState)
  }

  handleClick (statusItem, value, callback) {
    const newState = {}
    newState[statusItem] = value
    const ajaxUpdate = {}
    ajaxUpdate[statusItem] = value
    AjaxUpdateProperty(GetUpdateURL('epic', this.props.id), ajaxUpdate, () => {
      this.setState(newState)
      callback()
    })
  }

  handleStoryClick (storyId, statusItem, value, callback) {
    const newState = this.state.story
    const storyIndex = newState.findIndex((story) => story.id === storyId)
    if (!storyIndex) {
      console.error('Could not find story with that index')
      return
    }
    newState[storyIndex][statusItem] = value
    const ajaxUpdate = {}
    ajaxUpdate[statusItem] = value
    AjaxUpdateProperty(GetUpdateURL('story', storyId), ajaxUpdate, () => {
      this.setState(newState)
      callback()
    })
  }

  handleTaskClick (storyId, taskId, statusItem, value, callback) {
    console.log(storyId, taskId, statusItem, value, callback)
    const newState = this.state.story
    const storyIndex = newState.findIndex((story) => story.id === storyId)
    const taskIndex = storyIndex ? newState[storyIndex].tasks.findIndex((task) => task.id === taskId) : null
    if (!storyIndex || !taskIndex) {
      console.error('Could not find story or task with that index')
      return
    }
    const ajaxUpdate = {}
    ajaxUpdate[statusItem] = value
    newState[storyIndex].tasks[taskIndex][statusItem] = value
    AjaxUpdateProperty(GetUpdateURL('task', taskId), ajaxUpdate, () => {
      this.setState(newState)
      callback()
    })
  }

  close (type, id, archive, callback) {
    let newState, storyIndex//, taskIndex, epicIndex
    if (type === 'story') {
      newState = this.state.story
      storyIndex = newState.findIndex((story) => story.id === id)
      newState[storyIndex].closure_state = archive ? 'Closed' : null
    } else {
      console.error('Type is not supported')
      return
    }
    if (!archive) {
      console.log('Archiving story ' + id)
      AjaxUpdateProperty(GetCloseURL(type, id), id, () => {
        this.setState(newState)
        callback()
      })
    } else {
      console.log('Un-archiving story ' + id)
      AjaxDelete(GetCloseURL(type, id), id, () => {
        this.setState(newState)
        callback()
      })
    }
  }
}

export {
  CreateEpicButton,
  EpicContainer,
  CreateEpic
}
