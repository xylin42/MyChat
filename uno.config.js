import {defineConfig, presetWind4, presetIcons} from 'unocss'
import {presetDaisy} from "@ameinhardt/unocss-preset-daisy"

export default defineConfig({
    content: {
        filesystem: [
            'mychat/templates/**/*.html'
        ]
    },
    safelist: [
        'input', 'input-neutral'
    ],
    presets: [
        presetWind4(),
        presetDaisy(),
        presetIcons({
            collections: {
                'mdi': () => import('@iconify-json/mdi/icons.json').then(i=>i.default),
                'line-md': () => import('@iconify-json/line-md/icons.json').then(i=>i.default),
            }
        })
    ]
})