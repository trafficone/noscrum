import app from './app.jsx'
import taskSC from './task_showcase.jsx'
import sprintSC from './sprint_showcase.jsx'
import React from 'react'
import axios from 'axios'
import ReactDOM from 'react-dom/client'
// import ReactModal from 'react-modal'

const PrettyAlert = app.PrettyAlert
const TaskShowcase = taskSC.TaskShowcase
const SprintShowcase = sprintSC.SprintShowcase
/* const root = ReactDOM.createRoot(document.getElementById('reactComponents'))
root.render(<TaskShowcase epics={taskSC.noscrumObj} />) */

async function getSprintTasks (sprintId) {
  await axios.get(`/sprint/${sprintId}?is_json=true`)
    .then((resp) => {
      return resp.data.tasks
    })
    .catch((error) => {
      if (error.response.status === 404) {
        return []
      } else {
        PrettyAlert('Could not get Sprint')
      }
    })
}

async function getSprintSchedule (sprintId) {
  await axios.get(`/sprint/schedule/${sprintId}?is_json=true`)
    .then((resp) => {
      return resp.data.schedule_tasks
    })
    .catch((error) => {
      if (error.response.status === 404) {
        return []
      } else {
        PrettyAlert('Could not get Sprint Schedule')
      }
    })
}
module.exports = {
  getTestObj () { return taskSC.noscrumObj },
  TaskShowcase,
  PrettyAlert,
  renderTaskShowcase (showcaseId) {
    const root = ReactDOM.createRoot(document.getElementById(showcaseId))
    root.render(<TaskShowcase />)
  },

  renderSprintShowcase (showcaseId, sprintId) {
    let taskList
    let scheduleList
    Promise.all([
      getSprintTasks(sprintId),
      getSprintSchedule(sprintId)
    ]).then((results) => {
      taskList = results[0]
      scheduleList = results[1]
    })
    const root = ReactDOM.createRoot(document.getElementById(showcaseId))
    root.render(<SprintShowcase oTasks={taskList} oSchedule={scheduleList} />)
  }
}
