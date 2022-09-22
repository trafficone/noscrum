const gulp = require('gulp')
const browserify = require('browserify')
const babelify = require('babelify')
const source = require('vinyl-source-stream')
const concat = require('gulp-concat')

const cssFiles = [
  'node_modules/react-datepicker/dist/react-datepicker-min.module.css',
  'node_modules/foundation-sites/dist/css/foundation.min.css',
  'node_modules/foundation-sites/dist/css/foundation.min.css.map']

function clean (cb) {
  // clean the build area
  cb()
}

function buildJSX () {
  // build JSX components
  console.log('Buiding JSX')
  return browserify('jsx/index.jsx')
    .transform(babelify)
    .bundle()
    .pipe(source('app.js'))
    .pipe(gulp.dest('static/js'))
}

function css () {
  // bundle CSS components
  console.log('Bundling CSS')
  return gulp.src(cssFiles)
    .pipe(concat('style.css'))
    .pipe(gulp.dest('static/'))
}

exports.default = gulp.series(clean, buildJSX, css)
// if (process.env.NODE_ENV === 'production') {...productionstuff...}
