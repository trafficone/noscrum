'use strict;'
import { PropTypes } from 'prop-types'
import React from 'react'
import app from './app.jsx'
import StoryContainerTShowcase from './story.jsx'

const AjaxUpdateProperty = app.AjaxUpdateProperty
const GetUpdateURL = app.GetUpdateURL
const EditableHandleClick = app.EditableHandleClick
const CreateElementClick = app.CreateElementClick

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
    <div className="columns small-3">
      {props.label}:&nbsp;<span className="epic-metric">{props.value}</span>
    </div>
  )
}
EpicEstimateLabel.propTypes = { value: PropTypes.number.isRequired, label: PropTypes.string.isRequired }

class EpicEstimatesWidget extends React.Component {
  static propTypes = {
    tasks: PropTypes.array
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
      return <EpicEstimateLabel label={k[0]} key={v} value={k[1]} />
    }
    )
    return <div>{estimateLabels}</div>
  }
}

class EpicStoriesContainer extends React.Component {
  static propTypes = {
    updateTask: PropTypes.func,
    updateStory: PropTypes.func,
    stories: PropTypes.array
  }

  render () {
    const stories = this.props.stories
    const storyContainers = stories.map((story) => {
      return (
        <StoryContainerTShowcase
          key={story.id}
          id={story.id}
          prioritization={story.prioritization}
          story={story.story}
          deadline={story.deadline}
          tasks={story.tasks}
          update={(s, v, c) => this.props.updateStory(story.id, s, v, c)}
          updateTask={(t, s, v, c) => this.props.updateTask(story.id, t, s, v, c)}
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
class EpicCreateStoryButton extends React.Component {
  static propTypes = {
    create_url: PropTypes.string
  }

  render () {
    return (
      <button
        className="button create create-story"
        onClick={(t) => CreateElementClick(t, this.props.create_url)}
      >
        Create Story
      </button>
    )
  }
}

class CreateEpicButton extends React.Component {
  static propTypes = {
    create_url: PropTypes.string
  }

  render () {
    return (
      <button
        className="button create create-epic"
        onClick={(t) => CreateElementClick(t, this.props.create_url)}
      >
        Create Epic
      </button>
    )
  }
}

class EpicContainer extends React.Component {
  static propTypes = {
    id: PropTypes.number.isRequired,
    oEpic: PropTypes.string.isRequired,
    oColor: PropTypes.string,
    oStories: PropTypes.array
  }

  constructor (props) {
    super(props)
    const origColor = props.oColor ? props.oColor : 'green'
    this.state = {
      epic: props.oEpic,
      color: origColor,
      story: props.oStories
    }
  }

  render () {
    const stories = this.state.story
    const tasksAgg = stories.reduce((agg, story) => {
      return agg.concat(story.tasks)
    }, [])
    return (
      <div className={'epic ' + this.state.color}>
        <div className="row">
          <EpicNameLabel
            epic={this.state.epic}
            update={(c, v) => this.handleClick('epic', c, v)}
          />
          <EpicEstimatesWidget tasks={tasksAgg} />
        </div>
        <EpicStoriesContainer
          stories={stories}
          updateStory={(st, s, v, c) => this.handleStoryClick(st, s, v, c)}
          updateTask={(st, t, s, v, c) => this.handleTaskClick(st, t, s, v, c)}/>
        <EpicCreateStoryButton create_url={'/story/create/' + this.props.id + '?is_asc=true'} />
      </div>
    )
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
    newState[storyIndex][statusItem] = value
    const ajaxUpdate = {}
    ajaxUpdate[statusItem] = value
    AjaxUpdateProperty(GetUpdateURL('story', newState[storyIndex].id), ajaxUpdate, () => {
      this.setState(newState)
      callback()
    })
  }

  handleTaskClick (storyId, taskId, statusItem, value, callback) {
    console.log(storyId, taskId, statusItem, value, callback)
    const newState = this.state.story
    const storyIndex = newState.findIndex((story) => story.id === storyId)
    const taskIndex = newState[storyIndex].tasks.findIndex((task) => task.id === taskId)
    const ajaxUpdate = {}
    ajaxUpdate[statusItem] = value
    newState[storyIndex].tasks[taskIndex][statusItem] = value
    AjaxUpdateProperty(GetUpdateURL('task', newState[storyIndex].tasks[taskIndex].id), ajaxUpdate, () => {
      this.setState(newState)
      callback()
    })
  }
}

export default {
  CreateEpicButton,
  EpicContainer
}
