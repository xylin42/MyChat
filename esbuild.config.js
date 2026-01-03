import esbuild from 'esbuild'

esbuild.build({
    entrypPoints: {
        main: 'static/src/main.js'
    },
    outdir: 'static/dist',
})