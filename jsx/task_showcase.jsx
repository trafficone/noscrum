'use strict'
import React from 'react'
import ReactModal from 'react-modal'
import axios from 'axios'
import Skeleton from 'react-loading-skeleton'
import { EpicContainer, CreateEpicButton } from './epic.jsx'
import app from './app.jsx'
import { PropTypes } from 'prop-types'
import DatePicker from 'react-datepicker'

const PrettyAlert = app.PrettyAlert
const contextObject = app.contextObject
const baseFilter = {
  status: {
    'To-Do': false,
    'In Progress': false,
    Done: true
  },
  startDate: null,
  endDate: null
}

class SprintPlanButton extends React.Component {
  static propTypes = {
    update: PropTypes.func,
    isPlanningNow: PropTypes.bool.isRequired
  }

  constructor (props) {
    super(props)
    this.state = {
      modalOpen: false
    }
  }

  openPlan () {
    this.setState({ ...this.state, modalOpen: true })
  }

  close () {
    this.setState({ ...this.state, modalOpen: false })
  }

  render () {
    let clickFunc = () => this.openPlan()
    let planMsg = 'Plan Sprint'
    if (this.props.isPlanningNow) {
      console.log('currently planning')
      clickFunc = () => this.props.update(0)
      planMsg = 'End Planning'
    }
    return (
      <div>
        <button className="button" onClick={clickFunc}>
          { planMsg }
        </button>
        <SprintPlanMdl
          isOpen={this.state.modalOpen}
          close={() => this.close()}
          update={(f) => this.props.update(f)}/>
      </div>
    )
  }
}

class SprintPlanMdl extends React.Component {
  static propTypes = {
    isOpen: PropTypes.bool,
    close: PropTypes.func,
    update: PropTypes.func.isRequired
  }

  constructor (props) {
    super(props)
    this.state = {
      selectedDay: new Date()
    }
  }

  updatePlannedSprint () {
    const week = this.getWeekForDay(this.state.selectedDay)
    const dates = {
      startDate: this.dateToString(week[0]),
      endDate: this.dateToString(week[6])
    }
    axios.post('/sprint/create',
      {
        start_date: dates.startDate,
        end_date: dates.endDate
      })
      .then((result) => {
        this.props.update(result.data.sprint_id)
        this.props.close()
      })
  }

  dateToString (inDate) {
    const ye = new Intl.DateTimeFormat('en', { year: 'numeric' }).format(inDate)
    const mo = new Intl.DateTimeFormat('en', { month: '2-digit' }).format(inDate)
    const da = new Intl.DateTimeFormat('en', { day: '2-digit' }).format(inDate)
    return (`${ye}-${mo}-${da}`)
  }

  getWeekForDay (inDate) {
    const dowStart = (inDate.getDay() + 6) % 7
    const dayInMs = 24 * 3600 * 1000
    const monday = new Date(inDate.valueOf() - (dowStart) * dayInMs)
    const weekdays = Array.from(Array(7), (x, i) => new Date(monday.valueOf() + (i * dayInMs)))
    return weekdays
  }

  render () {
    return (
      <ReactModal isOpen={this.props.isOpen}
      style={{
        content: {
          width: '50%',
          minwidth: '10em'
        }
      }}>
        <h3>Select Sprint</h3>
        <p>Week of Sprint {'please select sprint'}</p>
        <DatePicker
          selected={this.state.selectedDay}
          onChange={(date) => this.setState({ ...this.state, selectedDay: date })}
          weekLabel='Sprint'
          highlightDates={this.getWeekForDay(this.state.selectedDay)}
          placeholderText="This highlights a week ago and a week from today"
          inline
        />
        <button className="button" onClick={() => this.updatePlannedSprint()}>Plan Sprint</button>
        <button className="close-button" onClick={() => this.props.close()} aria-label="Close"><span aria-hidden="true">&times;</span></button>
      </ReactModal>
    )
  }
}

class ShowcaseFilterStatusMdl extends React.Component {
  static propTypes = {
    isOpen: PropTypes.bool.isRequired,
    close: PropTypes.func.isRequired,
    update: PropTypes.func,
    prevFilter: PropTypes.object
  }

  constructor (props) {
    super(props)
    this.state = { filter: props.prevFilter }
  }

  handleSubmit () {
    this.props.update(this.state.filter)
    this.props.close()
  }

  render () {
    if (!this.props.isOpen) {
      return
    }
    const statusList = this.state.filter.status
    const statFilterBtns = Object.keys(statusList).map((v, index) => {
      const maybeHollow = statusList[v] ? 'hollow' : ''
      return (
          <button key={index}
                  className={'button ' + maybeHollow}
                  onClick={() => {
                    statusList[v] = !statusList[v]
                    this.setState({ ...this.state, filter: { ...this.state.filter, status: statusList } })
                  }}
          >{ v }</button>
      )
    })
    return (
    <ReactModal isOpen={this.props.isOpen}
      style={{
        content: {
          width: '50%',
          minwidth: '10em'
        }
      }}>
        <h3>Filters</h3>
        <fieldset className="cell medium-6 fieldset">
          <legend>Status Filters</legend>
          {statFilterBtns}
        </fieldset>
          <fieldset className="cell medium-6 fieldset">
            <legend>Deadline Filters</legend>
            <div className="input-group">
              <span className="input-group-label">Due Between</span>
              <input type="date" className="input-group-field"
                value={this.state.filter.startDate ? this.state.filter.startDate : ''}
                onChange={(t) => this.setState({ ...this.state, filter: { ...this.state.filter, startDate: t.target.value } })} />
              <span className="input-group-label"> and</span>
              <input type="date" className="input-group-field"
                value={this.state.filter.endDate ? this.state.filter.endDate : ''}
                onChange={(t) => this.setState({ ...this.state, filter: { ...this.state.filter, endDate: t.target.value } })} />
              <div className="input-group-button">
              </div>
            </div>
            <h4>Quick Deadline Filters</h4>
            <div className="button-group">
              <button
                className="button next_filter"
                onClick={() => {
                  const today = new Date()
                  const weekOut = new Date(today.getTime() + 7 * 24 * 3600 * 1000)
                  this.setState({
                    ...this.state,
                    filter: {
                      ...this.state.filter,
                      startDate: today.toISOString().substring(0, 10),
                      endDate: weekOut.toISOString().substring(0, 10)
                    }
                  })
                }
                }
                >Due in 1 Weeks
              </button>
              <button
                className="button next_filter"
                onClick={() => {
                  const today = new Date()
                  const twoWeekOut = new Date(today.getTime() + 2 * 7 * 24 * 3600 * 1000)
                  this.setState({
                    ...this.state,
                    filter: {
                      ...this.state.filter,
                      startDate: today.toISOString().substring(0, 10),
                      endDate: twoWeekOut.toISOString().substring(0, 10)
                    }
                  })
                }
                }
                >Due in 2 Weeks
              </button>
              <button
                className="button next_filter"
                onClick={() => {
                  const today = new Date()
                  const fourWeekOut = new Date(today.getTime() + 4 * 7 * 24 * 3600 * 1000)
                  this.setState({
                    ...this.state,
                    filter: {
                      ...this.state.filter,
                      startDate: today.toISOString().substring(0, 10),
                      endDate: fourWeekOut.toISOString().substring(0, 10)
                    }
                  })
                }
                }

                >Due in 4 Weeks
              </button>
            </div>
          </fieldset>
        <div className="button-group">
          <button className="button" onClick={() => this.handleSubmit()}>Filter</button>
        </div>
        <button className="close-button" onClick={() => this.props.close()} aria-label="Close"><span aria-hidden="true">&times;</span></button>
    </ReactModal>
    )
  }
}
ShowcaseFilterStatusMdl.contextType = app.contextObject

class ShowcaseFilterBtn extends React.Component {
  static propTypes = {
    update: PropTypes.func,
    prevFilter: PropTypes.object
  }

  constructor (props) {
    super(props)
    this.state = { modalOpen: false }
  }

  openFilter () {
    this.setState({ ...this.state, modalOpen: true })
  }

  close () {
    this.setState({ ...this.state, modalOpen: false })
  }

  render () {
    return (
      <div>
      <button className="button" onClick={() => this.openFilter()}>Open Filter</button>
      <ShowcaseFilterStatusMdl
        isOpen={this.state.modalOpen}
        close={() => this.close()}
        update={(f) => this.props.update(f)}
        prevFilter={this.props.prevFilter}
        />
      </div>
    )
  }
}

async function getUserTasks () {
  try {
    const resp = await axios.get('/task/?is_json=true')
    return resp.data.epics
  } catch (error) {
    if (error.response.status === 404) {
      return []
    } else {
      PrettyAlert('Could not get user Tasks')
    }
  }
}

class TaskShowcase extends React.Component {
  static propTypes = {
  }

  constructor (props) {
    super(props)
    this.state = {
      epic_list: [],
      context: 'TaskShowcase',
      sprintPlanning: 0,
      filter: { ...baseFilter }
    }
  }

  render () {
    const epics = this.state.epic_list
    let epicContainers
    if (epics.length === 0) {
      getUserTasks().then((epics) => {
        if (epics.length !== 0) {
          this.setState({ ...this.state, epic_list: epics })
        } else {
          this.setState({ ...this.state, epic_list: [{ epic: 'No Epic Found' }] })
        }
      })
      epicContainers = (
        <div>
          <Skeleton count={4} />
        </div>
      )
    } else {
      epicContainers = epics.map((epic, index) => {
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
    }
    return (
      <div className="content">
        <header>
        <SprintPlanButton update={(sprint) => this.setSprintPlanning(sprint)}
                          isPlanningNow={this.state.sprintPlanning > 0}/>
        <div className="button-group align-right">
        <ShowcaseFilterBtn
          prevFilter={this.state.filter}
          update={(f) => this.updateFilterState(f)} />
        </div>
        </header>
        <contextObject.Provider value={this.state} >
          {epicContainers}
        </contextObject.Provider>
        <CreateEpicButton addEpic={(e) => this.addEpic(e)} />
      </div>
    )
  }

  addEpic (epic) {
    const newstate = this.state
    newstate.epic_list.push(epic)
    this.setState(newstate)
  }

  setSprintPlanning (isPlanning) {
    this.setState({ ...this.state, sprintPlanning: isPlanning })
  }

  updateFilterState (newFilter) {
    this.setState({ ...this.state, filterObject: newFilter })
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

export default { TaskShowcase, noscrumObj, working: 'YES I AM WORKING', contextObject }
