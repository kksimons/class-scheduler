You can either pull this down and run the streamlit, it or you can use docker and use the container as your API endpoint. I've made the docker image public so it _should_ work, I hope.
If you pull down the repo you will need to do a `pip install -r requirements.txt` to make sure you've got all dependencies installed.

## Docker (docker must be installed and running: https://docs.docker.com/desktop/install/windows-install/)
`docker pull kksimons/scheduler:latest`

This means you've got to post to port 80
`docker run -p 80:5000 kksimons/scheduler:latest`

## Run the Streamlit

This gets you the user interface if you'd rather use that. It is set up to hit localhost port 80 already

(you need to be in the app folder where it lives to do so)
`python -m streamlit run streamlit_app.py`

## Use Postman
The endpoint you want to test is: `http://localhost:80/api/v1/scheduler`

You will need to make sure you have `Content-Type` set to `application/json` in your headers or it won't work (didn't for me anyway)

![image](https://github.com/user-attachments/assets/22a867d9-481e-4a0f-bae2-60a38ab871b8)

In the body it is looking for num_employees, shifts_per_day, total_days, employee_types as an array of either "full_time" or "part_time"

![image](https://github.com/user-attachments/assets/c6caeb28-a821-4e92-8cd2-5545f101b381)
