'use strict'
import React from 'react'
import { PropTypes } from 'prop-types'
import { EpicContainer, CreateEpicButton } from './epic.jsx'

class SprintPlanButton extends React.Component {
  render () {
    return (<div><button className="button">PlanSprint</button></div>)
  }
}
class ShowcaseFilterWidget extends React.Component {
  render () {
    return (
    <div>
        Filter:<ShowcaseFilterStatusBtn />
        <ShowcaseFilterDeadlineBtn />
        <button className="button">Remove Filters</button>
    </div>
    )
  }
}
class ShowcaseFilterStatusBtn extends React.Component {
  render () {
    return (
      <button className="button">Filter Status</button>
    )
  }
}
class ShowcaseFilterDeadlineBtn extends React.Component {
  render () {
    return (
      <button className="button">Filter Deadline</button>
    )
  }
}

class TaskShowcase extends React.Component {
  static propTypes = {
    epics: PropTypes.array
  }

  constructor (props) {
    super(props)
    this.state = {
      filter_date_start: null,
      filter_date_end: null,
      filter_status: ['Done'],
      sprint_planning: false
    }
  }

  render () {
    const epics = this.props.epics
    const epicContainers = epics.map((epic) => {
      return (
      <EpicContainer
        key={epic.id}
        id={epic.id}
        oEpic={epic.epic}
        oColor={epic.color}
        oStories={epic.stories}
       />
      )
    })
    return (
      <div>
        <header>
        <h2>Task Showcase</h2>
        <SprintPlanButton />
        <ShowcaseFilterWidget />
        </header>

        {epicContainers}
        <CreateEpicButton create_url={'/epic/create/?is_asc=true'} />

      </div>
    )
  }
}

// const root = ReactDOM.createRoot(document.getElementById('task_showcase_test'))
const noscrumObj = [{
  id: 1,
  epic: 'Awesome Epic',
  color: 'green',
  stories: [
    {
      id: 97,
      story: 'Cool Story Bro',
      prioritization: 1,
      tasks: [
        {
          id: 5,
          task: 'Awesome Task',
          estimate: 2,
          recurring: false
        }
      ]
    },
    {
      id: 80,
      story: 'AMAZING Story Bro',
      prioritization: 4,
      tasks: [
        {
          id: 12,
          task: 'Awesomer Task',
          estimate: 2,
          recurring: false,
          status: 'To-Do'
        },
        {
          id: 22,
          task: 'Awesomest Task',
          estimate: 3,
          recurring: false,
          status: 'Done'
        }
      ]
    }
  ]
}]

export default { TaskShowcase, noscrumObj, working: 'YES I AM WORKING' }
