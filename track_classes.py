class Track:
    def __init__(
        self,
        name,
        image,
        length,
        num_corners,
        lap_record=None,
        track_direction=None,
        pit_lane_time=None,
        pit_lane_speed=None,
    ):
        self.name = name
        self.image = image
        self.length = length
        self.num_corners = num_corners
        self.lap_record = lap_record
        self.track_direction = track_direction
        self.pit_lane_time = pit_lane_time
        self.pit_lane_speed = pit_lane_speed

    def __str__(self):
        return self.name

Paul_Ricard = Track(
    "Circuit Paul Ricard",
    "paul_ricard.png",
    5.791,
    15,
    "1:39.914",
)

Zolder = Track(
    "Zolder",
    "zolder.png",
    4.004,
    10,
    "1:31.117",
)

Monza = Track(
    "Monza",
    "monza.png",
    5.793,
    10,
    "1:19.525",
)

Brands_Hatch = Track(
    "Brands Hatch",
    "brands_hatch.png",
    3.916,
    9,
    "1:09.593",
)

Silverstone = Track(
    "Silverstone",
    "silverstone.png",
    5.891,
    18,
    "1:30.874",
)

Misano = Track(
    "Misano",
    "misano.png",
    4.226,
    16,
    "1:33.138",
)

Spa_Francorchamps = Track(
    "Circuit Spa-Francorchamps",
    "spa.png",
    7.004,
    21,
    "1:47.263",
)

Hungaroring = Track(
    "Hungaroring",
    "hungaroring.png",
    4.381,
    14,
    "1:19.071",
)

Nuerburgring = Track(
    "Nürburgring",
    "nürburgring.png",
    5.137,
    17,
    "1:56.385",
)

Barcelona = Track(
    "Circuit de Barcelona-Catalunya",
    "barcelona.png",
    4.655,
    16,
    "1:21.670",
)

Kyalami = Track(
    "Kyalami",
    "kyalami.png",
    4.261,
    13,
    "1:17.578",
)

Mount_Panorama = Track(
    "Mount Panorama",
    "mount_panorama.png",
    6.213,
    23,
    "2:01.286",
)

Laguna_Seca = Track(
    "Laguna Seca",
    "laguna_seca.png",
    3.601,
    11,
    "1:07.722",
)

Suzuka = Track(
    "Suzuka",
    "suzuka.png",
    5.807,
    17,
    "1:30.983",
)

Imola = Track(
    "Imola",
    "imola.png",
    4.905,
    17,
    "1:15.484",
)

Zandvoort = Track(
    "Zandvoort",
    "zandvoort.png",
    4.320,
    15,
    "1:16.538",
)

Donington_Park = Track(
    "Donington Park",
    "Donington.png",
    4.023,
    12,
    "1:28.714",
)

Snetterton = Track(
    "Snetterton 300",
    "snetterton.png",
    4.779,
    12,
    "1:39.933",
)

Oulton_Park = Track(
    "Oulton Park",
    "oulton_park.png",
    4.307,
    17,
    "1:24.680",
)

Circuit_of_the_Americas = Track(
    "Circuit of the Americas",
    "cota.png",
    5.516,
    20,
    "1:36.169",
)

Watkins_Glen = Track(
    "Watkins Glen",
    "watkins_glen.png",
    5.552,
    11,
    "1:23.916",
)

Indianapolis = Track(
    "Indianapolis",
    "indianapolis.png",
    4.192,
    13,
    "1:10.399",
)

ALL_TRACKS = [
    Paul_Ricard,
    Zolder,
    Monza,
    Brands_Hatch,
    Silverstone,
    Misano,
    Spa_Francorchamps,
    Hungaroring,
    Nuerburgring,
    Barcelona,
    Kyalami,
    Mount_Panorama,
    Laguna_Seca,
    Suzuka,
    Imola,
    Zandvoort,
    Donington_Park,
    Snetterton,
    Oulton_Park,
    Circuit_of_the_Americas,
    Watkins_Glen,
    Indianapolis,
]