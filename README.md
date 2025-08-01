You can either pull this down and run the streamlit, it or you can use docker and use the container as your API endpoint. I've made the docker image public so it _should_ work, I hope.
If you pull down the repo you will need to do a `pip install -r requirements.txt` to make sure you've got all dependencies installed.

## Docker (docker must be installed and running: https://docs.docker.com/desktop/install/windows-install/)
`docker pull kksimons/class-scheduler:latest`

This means you've got to post to port 80
`docker run -p 80:5000 kksimons/class-scheduler:latest`

## Use Postman
The endpoint you want to test is: `http://localhost:80/api/v1/class-scheduler` or `http://localhost:80/api/v1/class-scheduler-optimal`

Curl Post:

`curl -X POST "http://localhost:80/api/v1/class-scheduler" \
-H "Content-Type: application/json" \
-d '{
  "courses": [
    {
      "course": "ITSC 320 Software Security",
      "sections": [
        {
          "day1": {
            "day": "Tu",
            "start": "13:00",
            "end": "15:50",
            "format": "in-person"
          },
          "day2": {
            "day": "Th",
            "start": "13:00",
            "end": "14:50",
            "format": "online"
          },
          "professor": "John O\'Loughlin"
        },
        {
          "day1": {
            "day": "M",
            "start": "10:00",
            "end": "11:50",
            "format": "online"
          },
          "day2": {
            "day": "W",
            "start": "10:00",
            "end": "12:50",
            "format": "in-person"
          },
          "professor": "John O\'Loughlin"
        },
        {
          "day1": {
            "day": "F",
            "start": "08:00",
            "end": "10:50",
            "format": "in-person"
          },
          "day2": {
            "day": "M",
            "start": "12:00",
            "end": "13:50",
            "format": "online"
          },
          "professor": "John O\'Loughlin"
        },
        {
          "day1": {
            "day": "Tu",
            "start": "10:00",
            "end": "11:50",
            "format": "online"
          },
          "day2": {
            "day": "Th",
            "start": "15:00",
            "end": "17:50",
            "format": "in-person"
          },
          "professor": "John O\'Loughlin"
        },
        {
          "day1": {
            "day": "S",
            "start": "08:00",
            "end": "09:50",
            "format": "online"
          },
          "day2": {
            "day": "M",
            "start": "18:00",
            "end": "20:50",
            "format": "in-person"
          },
          "professor": "Kokub Sultan"
        }
      ]
    },
    {
      "course": "CPRG 305 Software Testing and Deployment",
      "sections": [
        {
          "day1": {
            "day": "Tu",
            "start": "08:00",
            "end": "09:50",
            "format": "in-person"
          },
          "day2": {
            "day": "Th",
            "start": "08:00",
            "end": "09:50",
            "format": "online"
          },
          "professor": "Anthony Azimi"
        },
        {
          "day1": {
            "day": "M",
            "start": "08:00",
            "end": "09:50",
            "format": "online"
          },
          "day2": {
            "day": "W",
            "start": "12:00",
            "end": "13:50",
            "format": "in-person"
          },
          "professor": "Anthony Azimi"
        },
        {
          "day1": {
            "day": "M",
            "start": "10:00",
            "end": "11:50",
            "format": "online"
          },
          "day2": {
            "day": "Th",
            "start": "16:00",
            "end": "17:50",
            "format": "in-person"
          },
          "professor": "Majid Bahrehvar"
        },
        {
          "day1": {
            "day": "Tu",
            "start": "10:00",
            "end": "11:50",
            "format": "online"
          },
          "day2": {
            "day": "Th",
            "start": "18:00",
            "end": "19:50",
            "format": "in-person"
          },
          "professor": "Akash Patel"
        }
      ]
    },
    {
      "course": "INTP 302 Emerging Trends in Software Development",
      "sections": [
        {
          "day1": {
            "day": "F",
            "start": "10:00",
            "end": "11:50",
            "format": "online"
          },
          "day2": {
            "day": "Tu",
            "start": "14:00",
            "end": "15:50",
            "format": "in-person"
          },
          "professor": "Sarbjeet Brar"
        },
        {
          "day1": {
            "day": "F",
            "start": "08:00",
            "end": "09:50",
            "format": "in-person"
          },
          "day2": {
            "day": "Tu",
            "start": "12:00",
            "end": "13:50",
            "format": "online"
          },
          "professor": "Natalia Hassan"
        },
        {
          "day1": {
            "day": "Th",
            "start": "12:00",
            "end": "13:50",
            "format": "in-person"
          },
          "day2": {
            "day": "M",
            "start": "13:00",
            "end": "14:50",
            "format": "online"
          },
          "professor": "Iles Wade"
        },
        {
          "day1": {
            "day": "Tu",
            "start": "08:00",
            "end": "09:50",
            "format": "online"
          },
          "day2": {
            "day": "Th",
            "start": "08:00",
            "end": "09:50",
            "format": "in-person"
          },
          "professor": "Sarbjeet Brar"
        },
        {
          "day1": {
            "day": "S",
            "start": "08:00",
            "end": "09:50",
            "format": "online"
          },
          "day2": {
            "day": "M",
            "start": "18:00",
            "end": "19:50",
            "format": "in-person"
          },
          "professor": "Sola Akinbode"
        }
      ]
    },
    {
      "course": "CPSY 300 Operating Systems",
      "sections": [
        {
          "day1": {
            "day": "M",
            "start": "08:00",
            "end": "09:50",
            "format": "online"
          },
          "day2": {
            "day": "W",
            "start": "08:00",
            "end": "10:50",
            "format": "in-person"
          },
          "professor": "Helder Rodrigues de Oliveira"
        },
        {
          "day1": {
            "day": "Th",
            "start": "10:00",
            "end": "11:50",
            "format": "in-person"
          },
          "day2": {
            "day": "Tu",
            "start": "15:00",
            "end": "16:50",
            "format": "online"
          },
          "professor": "Helder Rodrigues de Oliveira"
        },
        {
          "day1": {
            "day": "F",
            "start": "14:00",
            "end": "15:50",
            "format": "online"
          },
          "day2": {
            "day": "M",
            "start": "15:00",
            "end": "17:50",
            "format": "in-person"
          },
          "professor": "Mohamed E Mohamed"
        },
        {
          "day1": {
            "day": "F",
            "start": "10:00",
            "end": "11:50",
            "format": "online"
          },
          "day2": {
            "day": "W",
            "start": "15:00",
            "end": "17:50",
            "format": "in-person"
          },
          "professor": "Rajani Phadtare"
        },
        {
          "day1": {
            "day": "S",
            "start": "08:00",
            "end": "09:50",
            "format": "online"
          },
          "day2": {
            "day": "Th",
            "start": "18:00",
            "end": "20:50",
            "format": "in-person"
          },
          "professor": "Ravi Garlapati"
        }
      ]
    },
    {
      "course": "PROJ 309 Capstone Project",
      "sections": [
        {
          "day1": {
            "day": "M",
            "start": "08:00",
            "end": "10:50",
            "format": "in-person"
          },
          "day2": {
            "day": "F",
            "start": "08:00",
            "end": "09:50",
            "format": "in-person"
          },
          "professor": "Anwar Alabbas"
        },
        {
          "day1": {
            "day": "Tu",
            "start": "10:00",
            "end": "11:50",
            "format": "in-person"
          },
          "day2": {
            "day": "F",
            "start": "12:00",
            "end": "14:50",
            "format": "in-person"
          },
          "professor": "Rajani Phadtare"
        },
        {
          "day1": {
            "day": "Tu",
            "start": "08:00",
            "end": "09:50",
            "format": "in-person"
          },
          "day2": {
            "day": "Th",
            "start": "13:00",
            "end": "15:50",
            "format": "in-person"
          },
          "professor": "Anwar Alabbas"
        },
        {
          "day1": {
            "day": "M",
            "start": "13:00",
            "end": "14:50",
            "format": "in-person"
          },
          "day2": {
            "day": "F",
            "start": "15:00",
            "end": "17:50",
            "format": "in-person"
          },
          "professor": "Anwar Alabbas"
        }
      ]
    }
  ],
  "exclude_weekend": true
}'
`
