<script>
import { Line } from 'vue-chartjs'

export default {
  extends: Line,
  props: {
    newUsers: {
      type: Array,
      required: true,
    },
    activeUsers: {
      type: Array,
      required: true,
    },
  },
  watch: {
    newUsers() {
      this.render()
    },
    activeUsers() {
      this.render()
    },
  },
  mounted() {
    this.render()
  },
  methods: {
    render() {
      const labels = []
      const day = 24 * 60 * 60 * 1000
      for (let i = 0; i < 30; i++) {
        const date = new Date(new Date().getTime() - day * i)
        labels.unshift(date.toISOString().substr(0, 10))
      }

      const newUserData = this.mapCount(labels, this.newUsers)
      const activeUserData = this.mapCount(labels, this.activeUsers)

      this.renderChart(
        {
          labels,
          datasets: [
            {
              label: 'New users',
              borderColor: '#59cd90',
              backgroundColor: 'transparent',
              color: '#9bf2c4',
              data: newUserData,
            },
            {
              label: 'Active users',
              borderColor: '#198dd6',
              backgroundColor: 'transparent',
              color: '#b4bac2',
              data: activeUserData,
            },
          ],
        },
        {
          responsive: true,
          maintainAspectRatio: false,
          legend: {
            align: 'start',
            position: 'bottom',
          },
          scales: {
            xAxes: [
              {
                type: 'time',
                time: {
                  parser: 'YYYY-MM-DD',
                  displayFormats: {
                    day: 'MMM D',
                  },
                  tooltipFormat: 'MMM D',
                  unit: 'day',
                },
              },
            ],
          },
        }
      )
    },
    mapCount(labels, values) {
      return labels.map((date1) => {
        for (let i = 0; i < values.length; i++) {
          if (date1 === values[i].date) {
            return values[i].count
          }
        }
        return 0
      })
    },
  },
}
</script>
