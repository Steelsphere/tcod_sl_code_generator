generates c++ libtcod code for saving and loading objects

usage: serialize_code_generator.py [directory of header files]

example output:


    void Building::serialize(TCODZip* zip) {
	    cost.serialize(zip); // Goods
	    zip->putInt(tier);
	    zip->putString(name.c_str());
	    zip->putString(initial.c_str());
	    zip->putColor(&color);
    }

    void Building::deserialize(TCODZip* zip) {
	    cost.deserialize(zip); // Goods
	    tier = zip->getInt();
	    name = zip->getString();
	    initial = zip->getString();
	    color = zip->getColor();
    }
