from quart import Blueprint, render_template

front = Blueprint('frontend', __name__)

@front.route('/')
@front.route('/home')
async def home():
    return await render_template('index.html', active='home')


@front.route('/kursansicht')
async def kursansicht():
    return await render_template('kursansicht.html', active='kursansicht')


@front.route('/settings')
async def settings():
    return await render_template('settings.html', active='settings')

@front.route('/shop')
async def shop():
    return await render_template('shop.html', active='shop')
