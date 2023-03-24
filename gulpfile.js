const gulp = require('gulp')
const browserify = require('browserify')
const babelify = require('babelify')
const source = require('vinyl-source-stream')
const concat = require('gulp-concat')

const cssFiles = [
  'node_modules/react-datepicker/dist/react-datepicker.min.css',
  'node_modules/foundation-sites/dist/css/foundation.min.css',
  'node_modules/react-loading-skeleton/dist/skeleton.css',
  'css/style.css'
]

function clean (cb) {
  // clean the build area
  console.log('Clean')
  cb()
}

function buildJSX () {
  // build JSX components
  console.log('Buiding JSX')
  return browserify()//, {require: require.resolve('ndex.jsx:app',{paths: ['./jsx/']})})
    .require('./jsx/index.jsx', {
      expose: 'app'
    })
    .transform(babelify, {
      presets: ['@babel/preset-env',
        '@babel/preset-react']
    })
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

if (process.env.NODE_ENV === 'production') {
  exports.build = gulp.series(clean, gulp.parallel(buildJSX, css))
} else if (process.env.WSL) {
  console.log('Dev Build Active -- WSL Mode')
  exports.build = gulp.series(clean, gulp.parallel(buildJSX, css))
} else {
  console.log('Dev Build Active -- watching')
  exports.build = gulp.watch('jsx/',
    gulp.series(clean, gulp.parallel(buildJSX, css))
  )
}
exports.default = exports.build
