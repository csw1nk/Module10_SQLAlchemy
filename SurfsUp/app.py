# Import the dependencies.
from flask import Flask, jsonify, url_for
import numpy as np
import datetime as dt
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///../Resources/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()
# Reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)


#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    image_path = url_for('static', filename='Weather_station.png')
    return (
        f"Welcome to the Corey's Hawaiian Climate Analysis API!!<br/>"
        f"Go to any of the available routes to see the data:<br/>"
        f"/api/v1.0/precipitation - Returns precipitation data for the last year.<br/>"
        f"/api/v1.0/stations - Lists all weather observation stations.<br/>"
        f"/api/v1.0/tobs - Lists temperature observations (tobs) for the last year from the most active station.<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt; - Calculates TMIN, TAVG, and TMAX between the start and end date provided.<br/>"
        f"Add the Start Date and End Date you want, example: /api/v1.0/2017-01-01/2017-01-31<br/><br/>"
        f"<img src='{image_path}' alt='Weather Station Image'>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = dt.datetime.strptime(most_recent_date, "%Y-%m-%d") - dt.timedelta(days=365)

    results = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).all()
    session.close()

    precipitation_dict = {date: prcp for date, prcp in results}
    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    results = session.query(Station.station).all()
    session.close()

    stations_list = list(np.ravel(results))
    return jsonify(stations=stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = dt.datetime.strptime(most_recent_date, "%Y-%m-%d") - dt.timedelta(days=365)
    
    most_active_station_id = session.query(Measurement.station).\
                          group_by(Measurement.station).\
                          order_by(func.count(Measurement.id).desc()).first()[0]

    results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station_id).\
        filter(Measurement.date >= one_year_ago).all()
    session.close()
    tobs_data = [{"date": result[0], "tobs": result[1]} for result in results]
    
    return jsonify({"station": most_active_station_id, "tobs": tobs_data})


@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def range_temp(start, end=None):
    session = Session(engine)
    
    # Determine the most recent date in the dataset if end date is not provided
    if end is None:
        end = session.query(func.max(Measurement.date)).scalar()

    # Convert start and end into datetime objects to ensure comparison is accurate
    start_date = dt.datetime.strptime(start, "%Y-%m-%d")
    end_date = dt.datetime.strptime(end, "%Y-%m-%d")

    # Query to calculate TMIN, TAVG, TMAX for dates between start and end
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
    results = session.query(*sel).filter(Measurement.date >= start_date, Measurement.date <= end_date).all()
    session.close()

    # Structure result in a dictionary for jsonify to return as JSON
    temp_data = {
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }

    return jsonify(temp_data)

if __name__ == '__main__':
    app.run(debug=True)