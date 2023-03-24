# NoScrum React Components
Quick rundown of the visual components of NoScrum React Components.
## App Component
Contains all items which are used in several places across the NoScrum webapp.
Exports:
-  EditableHandleClick: several clickable elements which are editable are handled here
-  AjaxUpdateProperty: simplify interaction with NoScrum API
-  GetUpdateURL: Update URL for several objects. A bit of a hack...
-  DeadlineLabel: Deadline label component used in stories and tasks
-  PrettyAlert: Pretty alert component. Available everywhere.
-  contextObject: React Context.
### Index
Contains items consumed by templates.
Exports:
- RenderTaskShowcase: Render the complete TaskShowcase React Component
- RenderSprintShowcase: Render the complete SprintShowcase React Component
- PrettyAlert
- getTestObj
- TaskShowcase: TaskShowcase object, used in testing
## Object-level components
### Epic
### Story
### Task
## Page-level Components
### Task Showcase
### Sprint Showcase
