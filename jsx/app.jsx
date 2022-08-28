'use strict'
import React from 'react'
import { string, func, bool } from 'prop-types'
import $ from 'jquery'
import DatePicker from 'react-datepicker'
import 'foundation-sites'

function GetUpdateURL (objectType, locatorId) {
  return `/${objectType}/${locatorId}?is_json=true`
}

function EditableHandleClick (t, origin) {
  const taskNameObj = origin
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
    const newValue = $(t.target).text().trim()
    taskNameObj.props.update(newValue, callbackFunc)
  })
}

function AjaxUpdateProperty (updateUrl, newValue, callback) {
  $.ajax({
    url: updateUrl,
    data: newValue,
    type: 'POST',
    dataType: 'json'
  }).done(function (json) {
    callback(json)
  }).fail(function (xhr, status, errorThrown) {
    PrettyAlert('Sorry, there was a problem!')
    console.log('Error: ' + errorThrown)
    console.log('Status: ' + status)
    console.dir(xhr)
  }).always(function (xhr, status) {
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
        <DatePicker
          title="Click To Edit"
          className={'deadline ' + this.props.update ? 'editable' : ''}
          onChange={this.props.update ? (d) => this.handleChange(d) : () => {}}
          // customInput={this.getDeadlineMessage()}
        />
    )
  }

  handleClick (newDate) {
    this.props.update(newDate, () => {})
  }

  getDeadlineMessage () {
    if (this.props.deadline === null) {
      const message = this.props.recurring ? 'No End Date Set' : 'No Deadline Set'
      return (<input type="text" value={message} />)
    }
    return (<input type="text" value={this.props.deadline} />)
  }
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

function CreateElementClick (t, getUrl) {
  $(t.target)
    .siblings('div')
    .load(getUrl, () => {
      console.log('Loaded ' + getUrl)
    })
  $(t.target).addClass('invisible')
}

export default {
  EditableHandleClick,
  CreateElementClick,
  AjaxUpdateProperty,
  GetUpdateURL,
  DeadlineLabel,
  PrettyAlert
}
