from flask import Flask, request, render_template, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
import sys
import os

# 添加父目录到路径，以便导入 config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

app = Flask(__name__)

# 配置 MySQL 数据库
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}/{config.DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# 定义数据库模型 - 对应实际的 stations 表
class DublinBikeStation(db.Model):
    __tablename__ = "stations"
    number = db.Column(db.BigInteger, primary_key=True)  # 站点编号
    contract_name = db.Column(db.String(255), nullable=True)  # 合约名称
    name = db.Column(db.String(255), nullable=True)  # 站点名称
    address = db.Column(db.String(500), nullable=True)  # 地址
    lat = db.Column(db.Float, nullable=True)  # 纬度
    lng = db.Column(db.Float, nullable=True)  # 经度

    def __repr__(self):
        return f"<Station {self.name}>"


# 定义数据库模型 - 对应实际的 availability 表
class Availability(db.Model):
    __tablename__ = "availability"
    # 使用 (number, snapshot_time) 作为复合主键
    number = db.Column(db.BigInteger, primary_key=True, index=True)  # 站点编号
    snapshot_time = db.Column(db.DateTime, primary_key=True, index=True)  # 快照时间
    bike_stands = db.Column(db.BigInteger, nullable=True)  # 自行车架总数
    available_bike_stands = db.Column(db.BigInteger, nullable=True)  # 可用架位
    available_bikes = db.Column(db.BigInteger, nullable=True)  # 可用自行车数
    status = db.Column(db.String(50), nullable=True)  # 站点状态
    last_update = db.Column(db.DateTime, nullable=True)  # 最后更新时间

    def __repr__(self):
        return f"<Availability station={self.number} time={self.snapshot_time}>"


# ==================== 原始路由 ====================
# 模版上下文
@app.route("/profile/<username>")
def profile(username):
    user = {"name": username, "age": 25}
    return render_template("profile.html", user=user)


@app.route("/")
def form():
    return render_template("form.html")


def home():
    return render_template("index.html", title="Welcome Page", name="John Doe")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form["username"]
        return f"Hello {name}, POST request received"
    return render_template("name.html")


@app.route("/custom_response")
def custom_response():
    response = make_response("This is a custom response!")
    response.headers["X-Custom-Header"] = "Value"
    return response


@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name")
    email = request.form.get("email")
    return f"Name: {name}, Email: {email}"


@app.route("/form", methods=["GET"])
def show_form():
    return render_template("form.html")


@app.route("/about")
def about():
    return "This is the About Page."


@app.route("/greet/<name>")
def greet(name):
    return f"Hello, {name}!"


# ==================== 数据库相关路由 ====================


@app.route("/init-db", methods=["GET"])
def init_db():
    """初始化数据库表（仅用于创建 dublinbike_status 等新表）"""
    try:
        with app.app_context():
            db.create_all()
        return "数据库表创建成功！（stations 表已存在，无需创建）"
    except Exception as e:
        return f"错误: {str(e)}", 500


@app.route("/add_station/<int:number>/<station_name>/<contract>", methods=["POST"])
def add_station(number, station_name, contract):
    """添加站点"""
    try:
        station = DublinBikeStation(
            number=number, name=station_name, contract_name=contract
        )
        db.session.add(station)
        db.session.commit()
        return jsonify({"message": f"Station {station_name} added successfully!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/stations", methods=["GET"])
def get_stations():
    """查询所有站点"""
    try:
        stations = DublinBikeStation.query.all()
        return jsonify(
            [
                {
                    "number": s.number,
                    "contract_name": s.contract_name,
                    "name": s.name,
                    "address": s.address,
                    "lat": s.lat,
                    "lng": s.lng,
                }
                for s in stations
            ]
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/station/<station_name>", methods=["GET"])
def get_station(station_name):
    """查询特定站点"""
    try:
        station = DublinBikeStation.query.filter_by(name=station_name).first()
        if station:
            return jsonify(
                {
                    "number": station.number,
                    "contract_name": station.contract_name,
                    "name": station.name,
                    "address": station.address,
                    "lat": station.lat,
                    "lng": station.lng,
                }
            )
        return jsonify({"error": "Station not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== Availability 相关路由 ====================


@app.route("/availability", methods=["GET"])
def get_availability():
    """查询所有站点的可用性数据"""
    try:
        availabilities = Availability.query.all()
        return jsonify(
            [
                {
                    "number": a.number,
                    "bike_stands": a.bike_stands,
                    "available_bike_stands": a.available_bike_stands,
                    "available_bikes": a.available_bikes,
                    "status": a.status,
                    "last_update": a.last_update.isoformat() if a.last_update else None,
                    "snapshot_time": (
                        a.snapshot_time.isoformat() if a.snapshot_time else None
                    ),
                }
                for a in availabilities
            ]
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/availability/<int:station_number>", methods=["GET"])
def get_station_availability(station_number):
    """查询特定站点的所有可用性历史数据（分页）"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)

        # 分页查询该站点的所有历史记录
        pagination = (
            Availability.query.filter_by(number=station_number)
            .order_by(Availability.snapshot_time.desc())  # 按时间倒序
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        if pagination.total == 0:
            return jsonify({"error": f"No data for station {station_number}"}), 404

        return jsonify(
            {
                "station_number": station_number,
                "page": page,
                "per_page": per_page,
                "total_records": pagination.total,
                "total_pages": pagination.pages,
                "results": [
                    {
                        "number": a.number,
                        "bike_stands": a.bike_stands,
                        "available_bike_stands": a.available_bike_stands,
                        "available_bikes": a.available_bikes,
                        "status": a.status,
                        "last_update": (
                            a.last_update.isoformat() if a.last_update else None
                        ),
                        "snapshot_time": (
                            a.snapshot_time.isoformat() if a.snapshot_time else None
                        ),
                    }
                    for a in pagination.items
                ],
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/availability/history/<int:station_number>", methods=["GET"])
def availability_history(station_number):
    """查询特定站点在时间范围内的可用性历史"""
    try:
        start_time = request.args.get(
            "start_time", type=str
        )  # 格式：2026-02-03T10:00:00
        end_time = request.args.get("end_time", type=str)
        limit = request.args.get("limit", 100, type=int)

        query = Availability.query.filter_by(number=station_number)

        # 按时间范围过滤
        if start_time:
            try:
                from datetime import datetime

                start_dt = datetime.fromisoformat(start_time)
                query = query.filter(Availability.snapshot_time >= start_dt)
            except:
                return (
                    jsonify(
                        {
                            "error": "Invalid start_time format. Use ISO format: 2026-02-03T10:00:00"
                        }
                    ),
                    400,
                )

        if end_time:
            try:
                from datetime import datetime

                end_dt = datetime.fromisoformat(end_time)
                query = query.filter(Availability.snapshot_time <= end_dt)
            except:
                return (
                    jsonify(
                        {
                            "error": "Invalid end_time format. Use ISO format: 2026-02-03T10:00:00"
                        }
                    ),
                    400,
                )

        results = query.order_by(Availability.snapshot_time.desc()).limit(limit).all()

        if not results:
            return (
                jsonify(
                    {
                        "message": f"No data for station {station_number} in this time range",
                        "count": 0,
                    }
                ),
                404,
            )

        return jsonify(
            {
                "station_number": station_number,
                "time_range": {
                    "start": start_time,
                    "end": end_time,
                },
                "count": len(results),
                "limit": limit,
                "results": [
                    {
                        "number": a.number,
                        "available_bikes": a.available_bikes,
                        "available_bike_stands": a.available_bike_stands,
                        "status": a.status,
                        "snapshot_time": (
                            a.snapshot_time.isoformat() if a.snapshot_time else None
                        ),
                    }
                    for a in results
                ],
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/availability/stats", methods=["GET"])
def availability_stats():
    """获取 availability 表的统计信息"""
    try:
        from sqlalchemy import func, distinct

        total_records = db.session.query(func.count(Availability.number)).scalar()
        unique_stations = db.session.query(
            func.count(distinct(Availability.number))
        ).scalar()

        return jsonify(
            {
                "total_records": total_records,
                "unique_stations": unique_stations,
                "avg_bikes_available": float(
                    db.session.query(func.avg(Availability.available_bikes)).scalar()
                    or 0
                ),
                "avg_stands_available": float(
                    db.session.query(
                        func.avg(Availability.available_bike_stands)
                    ).scalar()
                    or 0
                ),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/availability/stations/list", methods=["GET"])
def availability_stations_list():
    """获取所有有可用性数据的站点号列表"""
    try:
        from sqlalchemy import distinct

        stations = (
            db.session.query(distinct(Availability.number))
            .order_by(Availability.number)
            .all()
        )
        station_list = [s[0] for s in stations]

        return jsonify(
            {
                "total_stations": len(station_list),
                "station_numbers": station_list,
                "note": "use /availability/<number> to get specific station data",
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/availability/summary/<int:station_number>", methods=["GET"])
def availability_summary(station_number):
    """获取特定站点的可用性统计摘要"""
    try:
        from sqlalchemy import func

        records = Availability.query.filter_by(number=station_number).all()

        if not records:
            return jsonify({"error": f"No data for station {station_number}"}), 404

        # 计算统计数据
        bike_availability = [
            r.available_bikes for r in records if r.available_bikes is not None
        ]
        stand_availability = [
            r.available_bike_stands
            for r in records
            if r.available_bike_stands is not None
        ]

        return jsonify(
            {
                "station_number": station_number,
                "total_snapshots": len(records),
                "time_range": {
                    "earliest": (
                        min(
                            r.snapshot_time for r in records if r.snapshot_time
                        ).isoformat()
                        if any(r.snapshot_time for r in records)
                        else None
                    ),
                    "latest": (
                        max(
                            r.snapshot_time for r in records if r.snapshot_time
                        ).isoformat()
                        if any(r.snapshot_time for r in records)
                        else None
                    ),
                },
                "available_bikes": {
                    "min": min(bike_availability) if bike_availability else None,
                    "max": max(bike_availability) if bike_availability else None,
                    "avg": (
                        sum(bike_availability) / len(bike_availability)
                        if bike_availability
                        else None
                    ),
                },
                "available_stands": {
                    "min": min(stand_availability) if stand_availability else None,
                    "max": max(stand_availability) if stand_availability else None,
                    "avg": (
                        sum(stand_availability) / len(stand_availability)
                        if stand_availability
                        else None
                    ),
                },
                "status_distribution": {
                    status: sum(1 for r in records if r.status == status)
                    for status in set(r.status for r in records if r.status)
                },
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== 搜索功能 ====================


@app.route("/search", methods=["GET"])
def search():
    """通用搜索 - 搜索站点名称或地址"""
    query = request.args.get("query", "").strip()

    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    try:
        # 搜索站点名称或地址
        results = DublinBikeStation.query.filter(
            (DublinBikeStation.name.ilike(f"%{query}%"))
            | (DublinBikeStation.address.ilike(f"%{query}%"))
        ).all()

        if not results:
            return (
                jsonify({"message": f"No results found for: {query}", "count": 0}),
                404,
            )

        return jsonify(
            {
                "query": query,
                "count": len(results),
                "results": [
                    {
                        "number": s.number,
                        "name": s.name,
                        "address": s.address,
                        "lat": s.lat,
                        "lng": s.lng,
                        "contract_name": s.contract_name,
                    }
                    for s in results
                ],
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search/station", methods=["GET"])
def search_station():
    """搜索站点 - 按名称或地址"""
    query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    try:
        # 分页搜索
        pagination = DublinBikeStation.query.filter(
            (DublinBikeStation.name.ilike(f"%{query}%"))
            | (DublinBikeStation.address.ilike(f"%{query}%"))
        ).paginate(page=page, per_page=per_page, error_out=False)

        return jsonify(
            {
                "query": query,
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "results": [
                    {
                        "number": s.number,
                        "name": s.name,
                        "address": s.address,
                        "lat": s.lat,
                        "lng": s.lng,
                    }
                    for s in pagination.items
                ],
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search/availability", methods=["GET"])
def search_availability():
    """搜索可用性数据 - 按可用自行车数或状态"""
    min_bikes = request.args.get("min_bikes", 0, type=int)
    max_bikes = request.args.get("max_bikes", None, type=int)
    status = request.args.get("status", None, type=str)
    limit = request.args.get("limit", 20, type=int)

    try:
        query = Availability.query

        # 按可用自行车数范围过滤
        if min_bikes >= 0:
            query = query.filter(Availability.available_bikes >= min_bikes)

        if max_bikes is not None:
            query = query.filter(Availability.available_bikes <= max_bikes)

        # 按状态过滤
        if status:
            query = query.filter(Availability.status.ilike(f"%{status}%"))

        results = query.limit(limit).all()

        return jsonify(
            {
                "filters": {
                    "min_bikes": min_bikes,
                    "max_bikes": max_bikes,
                    "status": status,
                    "limit": limit,
                },
                "count": len(results),
                "results": [
                    {
                        "number": a.number,
                        "available_bikes": a.available_bikes,
                        "available_bike_stands": a.available_bike_stands,
                        "status": a.status,
                        "snapshot_time": (
                            a.snapshot_time.isoformat() if a.snapshot_time else None
                        ),
                    }
                    for a in results
                ],
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search/nearby", methods=["GET"])
def search_nearby():
    """搜索附近的站点 - 按坐标范围"""
    try:
        lat = request.args.get("lat", type=float)
        lng = request.args.get("lng", type=float)
        radius = request.args.get("radius", 0.01, type=float)  # 约 1km

        if lat is None or lng is None:
            return jsonify({"error": "lat and lng parameters are required"}), 400

        # 简单的矩形范围查询（不是真正的圆形距离）
        stations = DublinBikeStation.query.filter(
            (DublinBikeStation.lat >= lat - radius)
            & (DublinBikeStation.lat <= lat + radius)
            & (DublinBikeStation.lng >= lng - radius)
            & (DublinBikeStation.lng <= lng + radius)
        ).all()

        if not stations:
            return (
                jsonify(
                    {
                        "message": f"No stations found near ({lat}, {lng})",
                        "count": 0,
                    }
                ),
                404,
            )

        return jsonify(
            {
                "center": {"lat": lat, "lng": lng},
                "radius": radius,
                "count": len(stations),
                "results": [
                    {
                        "number": s.number,
                        "name": s.name,
                        "address": s.address,
                        "lat": s.lat,
                        "lng": s.lng,
                    }
                    for s in stations
                ],
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
