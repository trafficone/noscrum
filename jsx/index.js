import app from './app.jsx'
import taskSC from './task_showcase.jsx'
import sprintSC from './sprint_showcase.jsx'
import React from 'react'
import ReactDOM from 'react-dom/client'

const PrettyAlert = app.PrettyAlert
const TaskShowcase = taskSC.TaskShowcase
const SprintShowcase = sprintSC.SprintShowcase
/* const root = ReactDOM.createRoot(document.getElementById('reactComponents'))
root.render(<TaskShowcase epics={taskSC.noscrumObj} />) */
module.exports = {
  getTestObj () { return taskSC.noscrumObj },
  TaskShowcase,
  PrettyAlert,
  renderTaskShowcase (showcaseId, taskObject) {
    const root = ReactDOM.createRoot(document.getElementById(showcaseId))
    root.render(<TaskShowcase epics={taskObject} />)
  },
  renderSprintShowcase (showcaseId, taskList, scheduleList) {
    const root = ReactDOM.createRoot(document.getElementById(showcaseId))
    root.render(<SprintShowcase oTasks={taskList} oSchedule={scheduleList} />)
  }
}
