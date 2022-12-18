'use strict'
import React from 'react'
import { string, func, bool } from 'prop-types'
import $ from 'jquery'
import axios from 'axios'
import 'foundation-sites'

function GetUpdateURL (objectType, locatorId) {
  return `/${objectType}/${locatorId}?is_json=true`
}
// FIXME: React-ify these JQuery functions
function EditableHandleClick (t, origin, isNumeric) {
  if (isNumeric === undefined) {
    isNumeric = false
  }
  const taskNameObj = origin
  const oldValue = $(t.target).text()
  function callbackFunc () {
    $(t.target).attr('contentEditable', 'false')
    $(t.target).off('keydown')
    $(t.target).off('blur')
  }
  $(t.target).attr('contentEditable', 'true')
  $(t.target).trigger('focus')
  $(t.target).on('keydown', function (e) {
    if (e.key === 'Enter') {
      $(t.target).trigger('blur')
    }
  })
  $(t.target).on('blur', function (e) {
    let newValue = $(t.target).text().trim()
    if (isNumeric) {
      if (!isNaN(Number(newValue))) {
        newValue = Number(newValue)
      } else {
        $(t.target).text(oldValue)
        callbackFunc()
        return
      }
    }
    taskNameObj.props.update(newValue, callbackFunc)
  })
}

function PrettyAlert (message) {
  $('header').after(
    $('<div>')
      .text(message)
      .append(
        $('<button>')
          .addClass('close-button')
          .attr('data-close', '')
          .html('&times;')
          .foundation()
      )
      .addClass('callout alert')
      .attr('data-closable', '')
      .foundation()
  )
}

function AjaxUpdateProperty (updateUrl, newValue, callback) {
  axios.post(updateUrl, newValue)
    .then(function (json) {
      callback(json)
    }).catch(function (errorThrown) {
      PrettyAlert('Sorry, there was a problem!')
      console.log('Error: ' + errorThrown)
    }).then(function (xhr, status) {
      console.log('Request to update status complete!')
    })
}

class DeadlineLabel extends React.Component {
  // FIXME - React-specific DatePicker element instead
  static propTypes = {
    update: func,
    deadline: string,
    recurring: bool
  }

  render () {
    return (
        /* <DatePicker
          title="Click To Edit"
          className={'deadline ' + this.props.update ? 'editable' : ''}
          onChange={this.props.update ? (d) => this.handleChange(d) : () => {}}
          // customInput={this.getDeadlineMessage()}
        /> */
        <div>
        <label>Deadline
        <input type="date"
          value={this.props.deadline ? this.props.deadline : ''}
          onInput={this.props.update ? (d) => this.handleChange(d) : () => {}}
          onChange={() => {}}
          className={`deadline ${this.props.update ? 'editable' : ''}`} />
        </label>
        </div>
    )
  }

  handleChange (newDate) {
    this.props.update(newDate.target.value, () => {})
  }

  getDeadlineMessage () {
    if (this.props.deadline === null) {
      const message = this.props.recurring ? 'No End Date Set' : 'No Deadline Set'
      return (<input type="text" value={message} />)
    }
    return (<input type="text" value={this.props.deadline} />)
  }
}

const contextObject = React.createContext(
  {
    context: 'Uninitialized',
    filter: {},
    sprintPlanning: null
  })

export default {
  EditableHandleClick,
  AjaxUpdateProperty,
  GetUpdateURL,
  DeadlineLabel,
  PrettyAlert,
  contextObject
}
